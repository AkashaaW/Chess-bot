import os
import sys

import chess
import pygame

from bot import BotJob

SQUARE_SIZE = 80
BOARD_PIXELS = SQUARE_SIZE * 8
STATUS_HEIGHT = 40
WINDOW_WIDTH = BOARD_PIXELS
WINDOW_HEIGHT = BOARD_PIXELS + STATUS_HEIGHT
FPS = 30

PLAYER_COLOR = chess.WHITE
BOT_COLOR = chess.BLACK
BOT_DELAY_MS = 500

DIFFICULTIES = ["Easy", "Medium", "Hard"]

LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)

SELECTED_COLOR = (246, 246, 105, 150)
MOVE_DOT_COLOR = (20, 85, 30, 130)

STATUS_BG = (40, 40, 40)
STATUS_TEXT = (240, 240, 240)

MENU_BG = (49, 46, 43)
MENU_TITLE = (240, 240, 240)
BUTTON_COLOR = (90, 86, 82)
BUTTON_SELECTED = (129, 182, 76)
BUTTON_TEXT = (250, 250, 250)
START_COLOR = (70, 130, 200)

OVERLAY_COLOR = (0, 0, 0, 160)
PANEL_COLOR = (49, 46, 43)

WHITE_PIECE_FILL = (250, 250, 250)
WHITE_PIECE_TEXT = (30, 30, 30)
BLACK_PIECE_FILL = (40, 40, 40)
BLACK_PIECE_TEXT = (250, 250, 250)
PIECE_OUTLINE = (20, 20, 20)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "Images")

# Pause button sits at the right end of the status bar
PAUSE_RECT = pygame.Rect(
    WINDOW_WIDTH - 110,
    BOARD_PIXELS + 5,
    100,
    30,
)


# ------------------------------------------------------------ menus
def build_menu_rects():
    """Return ({difficulty: Rect}, start_rect), centered."""
    button_w, button_h, gap = 240, 56, 18
    x = (WINDOW_WIDTH - button_w) // 2
    y = 230
    difficulty_rects = {}
    for name in DIFFICULTIES:
        rect = pygame.Rect(x, y, button_w, button_h)
        difficulty_rects[name] = rect
        y += button_h + gap
    start_rect = pygame.Rect(x, y + 30, button_w, button_h + 4)
    return difficulty_rects, start_rect


def build_pause_rects():
    """Return (panel_rect, {button_name: Rect}) over the board."""
    button_w, button_h, gap = 240, 56, 18
    panel = pygame.Rect(0, 0, 300, 320)
    panel.center = (BOARD_PIXELS // 2, BOARD_PIXELS // 2)
    x = panel.centerx - button_w // 2
    y = panel.top + 80
    rects = {}
    for name in ["Resume", "Restart", "Main Menu"]:
        rect = pygame.Rect(x, y, button_w, button_h)
        rects[name] = rect
        y += button_h + gap
    return panel, rects


def draw_button(screen, rect, text, color, font):
    pygame.draw.rect(screen, color, rect, border_radius=10)
    label = font.render(text, True, BUTTON_TEXT)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)


def draw_menu(screen, title_font, button_font, difficulty,
              difficulty_rects, start_rect):
    screen.fill(MENU_BG)
    mid_x = WINDOW_WIDTH // 2

    title = title_font.render("Chess Bot", True, MENU_TITLE)
    screen.blit(title, title.get_rect(center=(mid_x, 110)))

    sub = button_font.render("Choose difficulty", True, MENU_TITLE)
    screen.blit(sub, sub.get_rect(center=(mid_x, 190)))

    for name, rect in difficulty_rects.items():
        if name == difficulty:
            color = BUTTON_SELECTED
        else:
            color = BUTTON_COLOR
        draw_button(screen, rect, name, color, button_font)

    draw_button(screen, start_rect, "Start", START_COLOR, button_font)


def draw_pause_menu(screen, button_font, panel, pause_rects):
    # Dim the board area, then draw the panel and its buttons
    size = (BOARD_PIXELS, BOARD_PIXELS)
    dim = pygame.Surface(size, pygame.SRCALPHA)
    dim.fill(OVERLAY_COLOR)
    screen.blit(dim, (0, 0))

    pygame.draw.rect(screen, PANEL_COLOR, panel, border_radius=14)
    title = button_font.render("Paused", True, MENU_TITLE)
    title_pos = (panel.centerx, panel.top + 42)
    screen.blit(title, title.get_rect(center=title_pos))

    for name, rect in pause_rects.items():
        if name == "Resume":
            color = START_COLOR
        else:
            color = BUTTON_COLOR
        draw_button(screen, rect, name, color, button_font)


# ------------------------------------------------------------ board
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
    size = (SQUARE_SIZE, SQUARE_SIZE)
    for color in "wb":
        for kind in "PNBRQK":
            name = color + kind
            path = os.path.join(IMAGE_DIR, name + ".png")
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                images[name] = pygame.transform.smoothscale(img, size)
            else:
                print("Missing image:", path)
    return images


def get_legal_targets(board, from_square):
    targets = {}
    for move in board.legal_moves:
        if move.from_square != from_square:
            continue
        if move.promotion is not None:
            if move.promotion != chess.QUEEN:
                continue
        targets[move.to_square] = move
    return targets


def draw_board(screen):
    for row in range(8):
        for col in range(8):
            if (row + col) % 2 == 0:
                color = LIGHT_SQUARE
            else:
                color = DARK_SQUARE
            rect = pygame.Rect(
                col * SQUARE_SIZE,
                row * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE,
            )
            pygame.draw.rect(screen, color, rect)


def draw_selected(screen, selected):
    if selected is None:
        return
    row, col = square_to_row_col(selected)
    size = (SQUARE_SIZE, SQUARE_SIZE)
    overlay = pygame.Surface(size, pygame.SRCALPHA)
    overlay.fill(SELECTED_COLOR)
    screen.blit(overlay, (col * SQUARE_SIZE, row * SQUARE_SIZE))


def draw_pieces(screen, board, font, images):
    for square, piece in board.piece_map().items():
        row, col = square_to_row_col(square)
        x = col * SQUARE_SIZE
        y = row * SQUARE_SIZE

        side = "w" if piece.color == chess.WHITE else "b"
        key = side + piece.symbol().upper()
        if key in images:
            screen.blit(images[key], (x, y))
            continue

        # Fallback: lettered circle if the image is missing
        half = SQUARE_SIZE // 2
        center = (x + half, y + half)
        if piece.color == chess.WHITE:
            fill = WHITE_PIECE_FILL
            text_color = WHITE_PIECE_TEXT
        else:
            fill = BLACK_PIECE_FILL
            text_color = BLACK_PIECE_TEXT
        radius = half - 10
        pygame.draw.circle(screen, fill, center, radius)
        pygame.draw.circle(screen, PIECE_OUTLINE, center, radius, 2)
        label = font.render(piece.symbol().upper(), True, text_color)
        screen.blit(label, label.get_rect(center=center))


def draw_move_hints(screen, board, targets):
    size = (SQUARE_SIZE, SQUARE_SIZE)
    overlay = pygame.Surface(size, pygame.SRCALPHA)
    half = SQUARE_SIZE // 2
    center = (half, half)
    for square, move in targets.items():
        overlay.fill((0, 0, 0, 0))
        if board.is_capture(move):
            pygame.draw.circle(
                overlay, MOVE_DOT_COLOR, center, half - 4, 6)
        else:
            pygame.draw.circle(
                overlay, MOVE_DOT_COLOR, center, SQUARE_SIZE // 6)
        row, col = square_to_row_col(square)
        screen.blit(overlay, (col * SQUARE_SIZE, row * SQUARE_SIZE))


def status_text(board, paused):
    if board.is_checkmate():
        if board.turn == chess.WHITE:
            winner = "Black"
        else:
            winner = "White"
        return "Checkmate! " + winner + " wins"
    if board.is_game_over():
        return "Game over: draw"
    if paused:
        return "Paused"
    if board.turn == PLAYER_COLOR:
        text = "Your move (White)"
        if board.is_check():
            text += " - you are in check"
        return text
    text = "Bot is thinking..."
    if board.is_check():
        text += " (bot in check)"
    return text


def draw_status(screen, board, status_font, paused):
    bar = pygame.Rect(0, BOARD_PIXELS, WINDOW_WIDTH, STATUS_HEIGHT)
    pygame.draw.rect(screen, STATUS_BG, bar)
    text = status_text(board, paused)
    label = status_font.render(text, True, STATUS_TEXT)
    pos = (12, BOARD_PIXELS + STATUS_HEIGHT // 2)
    screen.blit(label, label.get_rect(midleft=pos))
    draw_button(screen, PAUSE_RECT, "Pause", BUTTON_COLOR, status_font)


# ------------------------------------------------------------ main
def main():
    pygame.init()
    size = (WINDOW_WIDTH, WINDOW_HEIGHT)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Chess Bot")
    images = load_piece_images()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 36, bold=True)
    status_font = pygame.font.SysFont("arial", 22)
    title_font = pygame.font.SysFont("arial", 56, bold=True)
    button_font = pygame.font.SysFont("arial", 28, bold=True)

    difficulty_rects, start_rect = build_menu_rects()
    pause_panel, pause_rects = build_pause_rects()

    state = "menu"        # "menu", "game", or "paused"
    difficulty = "Easy"   # the selected difficulty is stored here

    board = chess.Board()
    selected = None
    targets = {}
    bot_job = None        # the bot's pending search, or None
    bot_job_start = 0     # time (ms) the current search started

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif (event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1):
                pos = event.pos

                # ---------- start screen ----------
                if state == "menu":
                    for name, rect in difficulty_rects.items():
                        if rect.collidepoint(pos):
                            difficulty = name
                    if start_rect.collidepoint(pos):
                        board = chess.Board()
                        selected = None
                        targets = {}
                        bot_job = None
                        state = "game"
                    continue

                # ---------- pause menu ----------
                if state == "paused":
                    if pause_rects["Resume"].collidepoint(pos):
                        state = "game"
                    elif pause_rects["Restart"].collidepoint(pos):
                        board = chess.Board()
                        selected = None
                        targets = {}
                        bot_job = None   # discard any pending result
                        state = "game"
                    elif pause_rects["Main Menu"].collidepoint(pos):
                        board = chess.Board()
                        selected = None
                        targets = {}
                        bot_job = None   # discard any pending result
                        state = "menu"
                    continue

                # ---------- game ----------
                if PAUSE_RECT.collidepoint(pos):
                    state = "paused"   # a running bot_job keeps going
                    continue

                if board.is_game_over():
                    continue
                if board.turn != PLAYER_COLOR:
                    continue

                square = pixel_to_square(pos)
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
                    if piece and piece.color == PLAYER_COLOR:
                        selected = square
                        targets = get_legal_targets(board, square)
                    else:
                        selected = None
                        targets = {}

        # ---------- update + draw ----------
        if state == "menu":
            draw_menu(screen, title_font, button_font, difficulty,
                      difficulty_rects, start_rect)
        else:
            # The bot only starts or finishes a move in "game" state,
            # so a result that arrives during a pause is held.
            bot_turn = (state == "game"
                        and not board.is_game_over()
                        and board.turn == BOT_COLOR)
            if bot_turn:
                now = pygame.time.get_ticks()
                if bot_job is None:
                    bot_job = BotJob(board, difficulty)
                    bot_job_start = now
                elif bot_job.done:
                    waited = now - bot_job_start
                    if waited >= BOT_DELAY_MS:
                        move = bot_job.move
                        bot_job = None
                        if move is not None and move in board.legal_moves:
                            board.push(move)

            draw_board(screen)
            draw_selected(screen, selected)
            draw_pieces(screen, board, font, images)
            draw_move_hints(screen, board, targets)
            paused = state == "paused"
            draw_status(screen, board, status_font, paused)
            if paused:
                draw_pause_menu(
                    screen, button_font, pause_panel, pause_rects)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()