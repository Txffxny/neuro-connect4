"""Run neurons vs an opponent for N games and log the quality of every move.

Examples:
    python experiment.py --condition feedback --games 10
    python experiment.py --condition random_feedback --games 10
    python experiment.py --condition none --games 10

Each neuron move is scored by the solver. We log whether it was one of the
best moves AND the chance a random player would have picked a best move in
that same position, so the baseline is exact rather than estimated.
"""
import argparse
import csv
import os
import random
import time
from datetime import datetime

import cl
import game
import neural

NEURONS, OPPONENT = game.P1, game.P2


def play_one_game(neurons, game_no, condition, opponent, depth, writer):
    board = game.Board()
    player = random.choice([NEURONS, OPPONENT])  # alternate who starts
    while True:
        if player == NEURONS:
            features = game.threat_features(board, NEURONS)
            counts = neural.present_board(neurons, features)
            legal = board.legal_moves()
            col = neural.choose_column(counts, legal)

            scores = game.score_moves(board, NEURONS, depth)
            best = game.best_moves(scores)
            good = col in best
            chance = len(best) / len(legal)

            if condition == "feedback":
                neural.give_feedback(neurons, good)
            elif condition == "random_feedback":
                neural.give_feedback(neurons, random.random() < chance)
            else:
                neural.rest(neurons, 1.0)  # same timing, no stimulation

            writer.writerow({
                "game": game_no, "move": board.moves, "condition": condition,
                "column": col, "good": int(good), "chance_good": round(chance, 3),
                "spikes": sum(counts), "counts": " ".join(map(str, counts)),
            })
        else:
            col = game.random_move(board) if opponent == "random" else game.solver_move(board, OPPONENT, 2)

        row = board.play(col, player)
        if board.is_win_at(row, col, player):
            return "neurons" if player == NEURONS else "opponent"
        if board.is_full():
            return "draw"
        player = game.other(player)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", choices=["feedback", "random_feedback", "none"], default="feedback")
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--opponent", choices=["random", "weak_solver"], default="random")
    ap.add_argument("--depth", type=int, default=4, help="solver depth used to judge moves")
    args = ap.parse_args()

    os.makedirs("results", exist_ok=True)
    stamp = datetime.now().strftime("%H%M%S")
    path = f"results/{args.condition}_{stamp}.csv"
    fields = ["game", "move", "condition", "column", "good", "chance_good", "spikes", "counts"]

    print(f"Simulator: {cl.is_simulator()}  |  condition: {args.condition}  |  logging to {path}")
    tally = {"neurons": 0, "opponent": 0, "draw": 0}
    start = time.time()
    with open(path, "w", newline="") as f, cl.open() as neurons:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for g in range(args.games):
            try:
                result = play_one_game(neurons, g, args.condition, args.opponent, args.depth, writer)
            except TimeoutError as err:
                # A timing hiccup shouldn't lose the whole run: keep the moves
                # already logged, skip the rest of this game, and carry on.
                f.flush()
                print(f"game {g + 1}/{args.games}: skipped after a timing error ({err})")
                continue
            f.flush()
            tally[result] += 1
            print(f"game {g + 1}/{args.games}: {result}   ({time.time() - start:.0f}s elapsed)")
    print("Final:", tally)


if __name__ == "__main__":
    main()
