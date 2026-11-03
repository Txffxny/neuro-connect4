"""Stage demo: a human plays Connect Four against the neurons in the terminal.

    python play.py
"""
import cl
import game
import neural

HUMAN, NEURONS = game.P1, game.P2

with cl.open() as neurons:
    board = game.Board()
    player = HUMAN
    print("You are X, the neurons are O.\n")
    while True:
        print(board.render(), "\n")
        if player == HUMAN:
            legal = board.legal_moves()
            col = -1
            while col not in legal:
                try:
                    col = int(input(f"Your move {legal}: "))
                except ValueError:
                    pass
        else:
            counts = neural.present_board(neurons, game.threat_features(board, NEURONS))
            col = neural.choose_column(counts, board.legal_moves())
            print(f"Neurons fired {counts} -> column {col}\n")
        row = board.play(col, player)
        if board.is_win_at(row, col, player):
            print(board.render())
            print("\nYou win!" if player == HUMAN else "\nThe neurons win!")
            break
        if board.is_full():
            print(board.render(), "\nDraw!")
            break
        player = game.other(player)
