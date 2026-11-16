import random
import threading
import traceback

import chess

MATE_SCORE = 100000
INF = float("inf")

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# Half-moves to look ahead for each searching difficulty
SEARCH_DEPTH = {"Medium": 2, "Hard": 3}


# ------------------------------------------------------------ moves
def candidate_moves(board):
    """Legal moves, skipping silly underpromotions."""
    return [
        m for m in board.legal_moves
        if m.promotion in (None, chess.QUEEN)
    ]


def order_moves(board, moves):
    """Captures first. Helps alpha-beta cut branches sooner."""
    return sorted(moves, key=lambda m: not board.is_capture(m))


def random_move(board):
    moves = candidate_moves(board)
    if not moves:
        return None
    return random.choice(moves)


# ---------------------------------------------------------- scoring
def material_score(board, bot_color):
    """Bot's piece values minus the opponent's."""
    total = 0
    for piece in board.piece_map().values():
        value = PIECE_VALUES[piece.piece_type]
        if piece.color == bot_color:
            total += value
        else:
            total -= value
    return total


def evaluate(board, bot_color, ply):
    """Score a position from the bot's point of view.

    Checkmate beats any material score. A mate found sooner scores
    higher (smaller ply). Draws score 0.
    """
    if board.is_checkmate():
        if board.turn == bot_color:
            return -(MATE_SCORE - ply)   # the bot is the one mated
        return MATE_SCORE - ply          # the bot delivered mate
    if board.is_game_over():
        return 0                         # stalemate and other draws
    return material_score(board, bot_color)


# ----------------------------------------------------------- search
def minimax(board, depth, alpha, beta, maximizing,
            bot_color, ply, prune):
    """Plain minimax. With prune=True it adds alpha-beta pruning.

    The board is changed with push/pop, so it ends up unchanged.
    """
    if depth == 0 or board.is_game_over():
        return evaluate(board, bot_color, ply)

    moves = order_moves(board, candidate_moves(board))

    if maximizing:
        best = -INF
        for move in moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, False,
                            bot_color, ply + 1, prune)
            board.pop()
            best = max(best, score)
            if prune:
                alpha = max(alpha, best)
                if alpha >= beta:
                    break
        return best

    best = INF
    for move in moves:
        board.push(move)
        score = minimax(board, depth - 1, alpha, beta, True,
                        bot_color, ply + 1, prune)
        board.pop()
        best = min(best, score)
        if prune:
            beta = min(beta, best)
            if alpha >= beta:
                break
    return best


def search_best_move(board, depth, prune):
    """Return (best_move, score) for the side to move."""
    bot_color = board.turn
    moves = candidate_moves(board)
    random.shuffle(moves)             # random choice among equal moves
    moves = order_moves(board, moves)

    best_move = None
    best_score = -INF
    alpha = -INF
    for move in moves:
        board.push(move)
        score = minimax(board, depth - 1, alpha, INF, False,
                        bot_color, 1, prune)
        board.pop()
        if score > best_score:
            best_score = score
            best_move = move
        if prune:
            alpha = max(alpha, best_score)
    return best_move, best_score


# -------------------------------------------------------- the bot
def choose_bot_move(board, difficulty="Easy"):
    """Pick a move for the side to move.

    Returns one legal chess.Move, or None if the game is over.
    The board you pass in is never changed.
    """
    if board.is_game_over():
        return None

    if difficulty == "Easy":
        return random_move(board)

    if difficulty in SEARCH_DEPTH:
        depth = SEARCH_DEPTH[difficulty]
        prune = difficulty == "Hard"
        search_board = board.copy()   # search on a copy
        move, _score = search_best_move(
            search_board, depth=depth, prune=prune)
        return move

    raise ValueError("Unknown difficulty: " + repr(difficulty))


# ------------------------------------------------ background thinking
class BotJob:
    """Runs choose_bot_move on a copy of the board in a thread.

    The window keeps responding while the bot thinks. Check .done,
    then read .move. To cancel, just stop using the job: the thread
    only writes into this object, never into the live board.
    """

    def __init__(self, board, difficulty):
        self.difficulty = difficulty
        self.move = None
        self.done = False
        self._board = board.copy()
        self._backup = board.copy()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            self.move = choose_bot_move(self._board, self.difficulty)
        except Exception:
            traceback.print_exc()
            self.move = random_move(self._backup)
        self.done = True