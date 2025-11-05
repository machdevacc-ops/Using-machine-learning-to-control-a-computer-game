CELL_SIZE = 64
AGENT_WIDTH = 48
AGENT_HEIGHT = 48
MARGIN = 80
FPS = 10

WHITE = (255, 255, 255)
GRID_COLOR = (200, 200, 200)
TILE_BASE_COLOR = (40, 40, 40)
GRID_LINE_COLOR = (25, 25, 25)
GRID_LINE_WIDTH = 5

#amount needs to be same as the amount of textures loaded for each type
RUBBLE_TYPE_AMOUNT = 5
WALL_TYPE_AMOUNT = 3
TRASH_TYPE_AMOUNT = 6

SCORE_FILE = "scores.txt"

TILE_SYMBOLS = {
    '#': 'wall',
    'S': 'start',
    'G': 'goal',
    'R': 'reset',
    'B': 'bonus',
    'E': 'rubble',
    'M': 'enemy',
    'A': 'random_tile'
}