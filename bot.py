import random

import chess


def choose_bot_move(board):
    """Pick a move for the side to move. Right now: random legal move.

    Receives a chess.Board and must return a chess.Move.
    """
    moves = [m for m in board.legal_moves
             if m.promotion in (None, chess.QUEEN)]  # avoid silly underpromotions
    return random.choice(moves)