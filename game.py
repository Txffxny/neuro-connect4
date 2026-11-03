"""Connect Four rules plus a small alpha-beta solver used to score every move."""
import random

ROWS, COLS = 6, 7
EMPTY, P1, P2 = 0, 1, 2
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]  # search centre columns first (faster pruning)


class Board:
    def __init__(self):
        self.grid = [[EMPTY] * COLS for _ in range(ROWS)]  # row 0 is the bottom
        self.heights = [0] * COLS
        self.moves = 0

    def copy(self):
        b = Board.__new__(Board)
        b.grid = [row[:] for row in self.grid]
        b.heights = self.heights[:]
        b.moves = self.moves
        return b

    def legal_moves(self):
        return [c for c in range(COLS) if self.heights[c] < ROWS]

    def play(self, col, player):
        row = self.heights[col]
        self.grid[row][col] = player
        self.heights[col] += 1
        self.moves += 1
        return row

    def undo(self, col):
        self.heights[col] -= 1
        self.grid[self.heights[col]][col] = EMPTY
        self.moves -= 1

    def is_win_at(self, row, col, player):
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            count = 1
            for sign in (1, -1):
                r, c = row + dr * sign, col + dc * sign
                while 0 <= r < ROWS and 0 <= c < COLS and self.grid[r][c] == player:
                    count += 1
                    r += dr * sign
                    c += dc * sign
            if count >= 4:
                return True
        return False

    def wins_if_played(self, col, player):
        if self.heights[col] >= ROWS:
            return False
        row = self.play(col, player)
        win = self.is_win_at(row, col, player)
        self.undo(col)
        return win

    def is_full(self):
        return self.moves == ROWS * COLS

    def render(self):
        symbols = {EMPTY: ".", P1: "X", P2: "O"}
        lines = [" ".join(symbols[self.grid[r][c]] for c in range(COLS)) for r in reversed(range(ROWS))]
        lines.append(" ".join(str(c) for c in range(COLS)))
        return "\n".join(lines)


def other(player):
    return P2 if player == P1 else P1


def _heuristic(board, player):
    """Cheap positional score: prefer pieces in the centre column."""
    centre = sum(1 for r in range(ROWS) if board.grid[r][3] == player)
    centre_opp = sum(1 for r in range(ROWS) if board.grid[r][3] == other(player))
    return (centre - centre_opp) * 3


def _negamax(board, player, depth, alpha, beta):
    legal = board.legal_moves()
    if not legal:
        return 0
    for c in legal:  # immediate win
        if board.wins_if_played(c, player):
            return 1000 - board.moves
    if depth == 0:
        return _heuristic(board, player)
    best = -10_000
    for c in CENTER_ORDER:
        if c not in legal:
            continue
        board.play(c, player)
        score = -_negamax(board, other(player), depth - 1, -beta, -alpha)
        board.undo(c)
        best = max(best, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return best


def score_moves(board, player, depth=4):
    """Return {column: score} for every legal move. Higher is better for `player`."""
    scores = {}
    for c in board.legal_moves():
        row = board.play(c, player)
        if board.is_win_at(row, c, player):
            scores[c] = 1000 - board.moves
        else:
            scores[c] = -_negamax(board, other(player), depth - 1, -10_000, 10_000)
        board.undo(c)
    return scores


def best_moves(scores):
    top = max(scores.values())
    return [c for c, s in scores.items() if s == top]


def solver_move(board, player, depth=4):
    return random.choice(best_moves(score_moves(board, player, depth)))


def random_move(board, player=None):
    return random.choice(board.legal_moves())


def threat_features(board, player):
    """Per column: [I win here, I block their win here, playing here hands them a win]."""
    opp = other(player)
    feats = []
    for c in range(COLS):
        if board.heights[c] >= ROWS:
            feats.append([0, 0, 0])
            continue
        win = board.wins_if_played(c, player)
        block = board.wins_if_played(c, opp)
        board.play(c, player)
        gift = board.wins_if_played(c, opp)  # opponent plays on top of us
        board.undo(c)
        feats.append([int(win), int(block), int(gift)])
    return feats
