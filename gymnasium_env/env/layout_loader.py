import random

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

def load_layout(file_path):
    "loads chars from txt file"
    with open(file_path, 'r') as f:
        return [list(line.strip()) for line in f.readlines()]

def get_tile_type(symbol):
    return TILE_SYMBOLS.get(symbol)

def parse_layout(grid, episode_successes, map_emptiness):
    DMG_TILES = []
    REWARD_TILES = []
    WALL_TILES = []
    RUBBLE_TILES = []
    START_POSITIONS = []
    ENEMY_POSITIONS = []
    WIN_TILE = None

    random_tile_targets = ['reset', 'bonus', 'enemy']
    random_weights = [0.3, 0.6, 0.1]

    # Update emptiness level based on curriculum
    if episode_successes > 1500:
        map_emptiness = 0.2
    elif episode_successes > 500:
        map_emptiness = 0.5

    for r, row in enumerate(grid):
        for c, symbol in enumerate(row):
            pos = (r, c)
            tile_type = get_tile_type(symbol)

            # makes the map more empty by not assinging a type to a random tile thus leaving it empty
            if tile_type == 'random_tile':
                if random.random() < map_emptiness:
                    continue
                tile_type = random.choices(random_tile_targets, weights=random_weights, k=1)[0]

            if tile_type == 'wall':
                WALL_TILES.append(pos)
            elif tile_type == 'start':
                START_POSITIONS.append(pos)
            elif tile_type == 'goal':
                WIN_TILE = pos
            elif tile_type == 'reset':
                DMG_TILES.append(pos)
            elif tile_type == 'bonus':
                REWARD_TILES.append(pos)
            elif tile_type == 'rubble':
                RUBBLE_TILES.append(pos)
            elif tile_type == 'enemy':
                ENEMY_POSITIONS.append(pos)

    return {
        "WALL_TILES": WALL_TILES,
        "START_POSITIONS": START_POSITIONS,
        "WIN_TILE": WIN_TILE,
        "DMG_TILES": DMG_TILES,
        "REWARD_TILES": REWARD_TILES,
        "RUBBLE_TILES": RUBBLE_TILES,
        "ENEMY_POSITIONS": ENEMY_POSITIONS,
        "map_emptiness": map_emptiness
    }