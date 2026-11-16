import os
import sys

import chess
import pygame

from bot import choose_bot_move

SQUARE_SIZE = 80
BOARD_PIXELS = SQUARE_SIZE * 8
STATUS_HEIGHT = 40
FPS = 30

PLAYER_COLOR = chess.WHITE
BOT_COLOR = chess.BLACK
BOT_DELAY_MS = 500  # pause before the bot moves so you can see it happen

LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)

SELECTED_COLOR = (246, 246, 105, 150)
MOVE_DOT_COLOR = (20, 85, 30, 130)

STATUS_BG = (40, 40, 40)
STATUS_TEXT = (240, 240, 240)

WHITE_PIECE_FILL = (250, 250, 250)
WHITE_PIECE_TEXT = (30, 30, 30)
BLACK_PIECE_FILL = (40, 40, 40)
BLACK_PIECE_TEXT = (250, 250, 250)
PIECE_OUTLINE = (20, 20, 20)

IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Images")


def square_to_row_col(square):
    col = chess.square_file(square)
    row = 7 - chess.square_rank(square)
    return row, col


def pixel_to_square(pos):
    x, y = pos
    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE
    if not (0 <= col < 8 and 0 <= row < 8):
        return None  # also covers clicks on the status bar
    return chess.square(col, 7 - row)


def load_piece_images():
    images = {}
    for color in "wb":
        for kind in "PNBRQK":
            name = color + kind
            path = os.path.join(IMAGE_DIR, name + ".png")
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                images[name] = pygame.transform.smoothscale(
                    img, (SQUARE_SIZE, SQUARE_SIZE))
            else:
                print("Missing image:", path)
    return images


def get_legal_targets(board, from_square):
    targets = {}
    for move in board.legal_moves:
        if move.from_square != from_square:
            continue
        if move.promotion is not None and move.promotion != chess.QUEEN:
            continue
        targets[move.to_square] = move
    return targets


def draw_board(screen):
    for row in range(8):
        for col in range(8):
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            pygame.draw.rect(screen, color,
                             (col * SQUARE_SIZE, row * SQUARE_SIZE,
                              SQUARE_SIZE, SQUARE_SIZE))


def draw_selected(screen, selected):
    if selected is None:
        return
    row, col = square_to_row_col(selected)
    overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    overlay.fill(SELECTED_COLOR)
    screen.blit(overlay, (col * SQUARE_SIZE, row * SQUARE_SIZE))


def draw_pieces(screen, board, font, images):
    for square, piece in board.piece_map().items():
        row, col = square_to_row_col(square)
        x = col * SQUARE_SIZE
        y = row * SQUARE_SIZE

        key = ("w" if piece.color == chess.WHITE else "b") + piece.symbol().upper()
        if key in images:
            screen.blit(images[key], (x, y))
            continue

        center = (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)
        if piece.color == chess.WHITE:
            fill, text_color = WHITE_PIECE_FILL, WHITE_PIECE_TEXT
        else:
            fill, text_color = BLACK_PIECE_FILL, BLACK_PIECE_TEXT
        radius = SQUARE_SIZE // 2 - 10
        pygame.draw.circle(screen, fill, center, radius)
        pygame.draw.circle(screen, PIECE_OUTLINE, center, radius, 2)
        label = font.render(piece.symbol().upper(), True, text_color)
        screen.blit(label, label.get_rect(center=center))


def draw_move_hints(screen, board, targets):
    overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    center = (SQUARE_SIZE // 2, SQUARE_SIZE // 2)
    for square, move in targets.items():
        overlay.fill((0, 0, 0, 0))
        if board.is_capture(move):
            pygame.draw.circle(overlay, MOVE_DOT_COLOR, center,
                               SQUARE_SIZE // 2 - 4, 6)
        else:
            pygame.draw.circle(overlay, MOVE_DOT_COLOR, center, SQUARE_SIZE // 6)
        row, col = square_to_row_col(square)
        screen.blit(overlay, (col * SQUARE_SIZE, row * SQUARE_SIZE))


def status_text(board):
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        return f"Checkmate! {winner} wins"
    if board.is_game_over():
        return "Game over: draw"
    if board.turn == PLAYER_COLOR:
        return "Your move (White)" + (" - you are in check" if board.is_check() else "")
    return "Bot is thinking..." + (" (bot in check)" if board.is_check() else "")


def draw_status(screen, board, status_font):
    pygame.draw.rect(screen, STATUS_BG,
                     (0, BOARD_PIXELS, BOARD_PIXELS, STATUS_HEIGHT))
    label = status_font.render(status_text(board), True, STATUS_TEXT)
    screen.blit(label, label.get_rect(
        midleft=(12, BOARD_PIXELS + STATUS_HEIGHT // 2)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((BOARD_PIXELS, BOARD_PIXELS + STATUS_HEIGHT))
    pygame.display.set_caption("Chess Bot")
    images = load_piece_images()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 36, bold=True)
    status_font = pygame.font.SysFont("arial", 22)

    board = chess.Board()
    selected = None
    targets = {}
    bot_ready_at = None  # time (ms) when the bot is allowed to move

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Ignore clicks when the game is over or it's the bot's turn
                if board.is_game_over() or board.turn != PLAYER_COLOR:
                    continue

                square = pixel_to_square(event.pos)
                if square is None:
                    continue

                if selected is not None and square in targets:
                    board.push(targets[square])
                    selected = None
                    targets = {}
                elif square == selected:
                    selected = None
                    targets = {}
                else:
                    piece = board.piece_at(square)
                    if piece is not None and piece.color == PLAYER_COLOR:
                        selected = square
                        targets = get_legal_targets(board, square)
                    else:
                        selected = None
                        targets = {}

        # Bot's turn: wait a moment, then play
        if not board.is_game_over() and board.turn == BOT_COLOR:
            now = pygame.time.get_ticks()
            if bot_ready_at is None:
                bot_ready_at = now + BOT_DELAY_MS
            elif now >= bot_ready_at:
                board.push(choose_bot_move(board))
                bot_ready_at = None

        draw_board(screen)
        draw_selected(screen, selected)
        draw_pieces(screen, board, font, images)
        draw_move_hints(screen, board, targets)
        draw_status(screen, board, status_font)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()