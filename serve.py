"""Stage demo: play Connect Four against the neurons in your browser.

    python serve.py

Opens http://127.0.0.1:8765 automatically. Press Ctrl + C in the terminal to stop.
The connection to the CL1 (or simulator) stays open the whole time, so each
neuron move only costs the stimulation and read-out time.
"""
import json
import random
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import cl
import game
import neural

PORT = 8765  # 8000 is used by the Cortical Labs visualiser
HUMAN, NEURONS = game.P1, game.P2
HERE = Path(__file__).parent

state = {"board": game.Board(), "turn": HUMAN, "over": None, "last": None,
         "score": {"human": 0, "neurons": 0, "draw": 0}}
neurons = None  # opened in main()


def snapshot(extra=None):
    b = state["board"]
    data = {
        "grid": b.grid,                     # row 0 is the bottom
        "turn": "human" if state["turn"] == HUMAN else "neurons",
        "over": state["over"],
        "last": state["last"],
        "legal": b.legal_moves(),
        "score": state["score"],
        "simulator": cl.is_simulator(),
    }
    if extra:
        data.update(extra)
    return data


def apply_move(col, player):
    b = state["board"]
    row = b.play(col, player)
    state["last"] = [row, col]
    if b.is_win_at(row, col, player):
        state["over"] = "human" if player == HUMAN else "neurons"
        state["score"][state["over"]] += 1
    elif b.is_full():
        state["over"] = "draw"
        state["score"]["draw"] += 1
    else:
        state["turn"] = game.other(player)


def neuron_move():
    b = state["board"]
    features = game.threat_features(b, NEURONS)
    for attempt in range(2):  # one retry if the device hiccups
        try:
            counts = neural.present_board(neurons, features)
            break
        except TimeoutError:
            if attempt == 1:
                raise
    col = neural.choose_column(counts, b.legal_moves())
    apply_move(col, NEURONS)
    return {"counts": counts, "chosen": col}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the terminal quiet
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = (HERE / "board.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/state":
            self.send_json(snapshot())
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        payload = json.loads(self.rfile.read(length) or b"{}")
        try:
            if self.path == "/new":
                state.update(board=game.Board(), over=None, last=None,
                             turn=NEURONS if payload.get("neurons_first") else HUMAN)
                self.send_json(snapshot())
            elif self.path == "/human":
                col = int(payload["col"])
                if state["over"] or state["turn"] != HUMAN or col not in state["board"].legal_moves():
                    self.send_json(snapshot({"error": "That move isn’t available."}), 400)
                    return
                apply_move(col, HUMAN)
                self.send_json(snapshot())
            elif self.path == "/neurons":
                if state["over"] or state["turn"] != NEURONS:
                    self.send_json(snapshot({"error": "It isn’t the neurons’ turn."}), 400)
                    return
                self.send_json(snapshot(neuron_move()))
            else:
                self.send_error(404)
        except Exception as err:  # show the problem in the page rather than crashing
            print("Error:", repr(err))
            self.send_json(snapshot({"error": f"The neurons didn’t respond ({type(err).__name__}). Try again."}), 500)


def main():
    global neurons
    with cl.open() as n:
        neurons = n
        server = None
        for port in range(PORT, PORT + 20):  # use the next free port if one is taken
            try:
                server = HTTPServer(("127.0.0.1", port), Handler)
                break
            except OSError:
                continue
        if server is None:
            raise SystemExit(f"No free port between {PORT} and {PORT + 19}.")
        url = f"http://127.0.0.1:{port}"
        print(f"Simulator: {cl.is_simulator()}")
        print(f"Board running at {url}  (Ctrl + C to stop)")
        webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
