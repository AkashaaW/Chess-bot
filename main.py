import os
import sys

import chess
import pygame

SQUARE_SIZE = 80
BOARD_PIXELS = SQUARE_SIZE * 8
FPS = 30

LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)

WHITE_PIECE_FILL = (250, 250, 250)
WHITE_PIECE_TEXT = (30, 30, 30)
BLACK_PIECE_FILL = (40, 40, 40)
BLACK_PIECE_TEXT = (250, 250, 250)
PIECE_OUTLINE = (20, 20, 20)

IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Images")


def square_to_row_col(square):
    """Convert a python-chess square (0-63) to a Pygame (row, col).

    White is at the bottom, so rank 1 maps to the bottom row (row 7).
    """
    col = chess.square_file(square)       # a=0 ... h=7
    row = 7 - chess.square_rank(square)   # rank 1 -> row 7, rank 8 -> row 0
    return row, col


def load_piece_images():
    """Load Images/wK.png ... bP.png, scaled to the square size."""
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


def draw_board(screen):
    for row in range(8):
        for col in range(8):
            is_light = (row + col) % 2 == 0
            color = LIGHT_SQUARE if is_light else DARK_SQUARE
            rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE,
                               SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(screen, color, rect)


def draw_pieces(screen, board, font, images):
    for square, piece in board.piece_map().items():
        row, col = square_to_row_col(square)
        x = col * SQUARE_SIZE
        y = row * SQUARE_SIZE

        key = ("w" if piece.color == chess.WHITE else "b") + piece.symbol().upper()
        if key in images:
            screen.blit(images[key], (x, y))
            continue

        # Fallback: lettered circle if the image is missing
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


def main():
    pygame.init()
    screen = pygame.display.set_mode((BOARD_PIXELS, BOARD_PIXELS))
    pygame.display.set_caption("Chess Bot")
    images = load_piece_images()  # must come after set_mode
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 36, bold=True)

    board = chess.Board()  # standard starting position

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        draw_board(screen)
        draw_pieces(screen, board, font, images)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()