import pygame
from game.config import CELL_SIZE, MARGIN, FPS

def render_game(game):
    rows, cols = game.grid_size
    window_width = cols * CELL_SIZE + MARGIN * 2
    window_height = rows * CELL_SIZE + MARGIN * 2

    if game.window is None:
        pygame.init()
        game.window = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("Grid World")
        game.clock = pygame.time.Clock()
        game.font = pygame.font.SysFont(None, 40)

        

    now = pygame.time.get_ticks()
    elapsed = now - game._last_poison_tick
    if elapsed > game.poison_frame_duration:
        game.poison_frame_index = (game.poison_frame_index + 1) % len(game.poison_frame_order)
        game._last_poison_tick = now

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()


    game.window.fill(game.background_color)
    game._draw_base_tiles()
    game._draw_grid()

    for tile in game.DMG_TILES:
        game._draw_poison(tile)

    for tile in game.REWARD_TILES:
        game._draw_trash(tile)

    game._draw_target_tile(game.WIN_TILE)

    for tile in game.WALL_TILES:
        game._draw_wall(tile)

    for tile in game.RUBBLE_TILES:
        game._draw_rubble(tile)

    for pos in game.ENEMY_POSITIONS:
        game._draw_enemy(pos)

    for pos in game.DANGER_TILES:
        game._draw_danger_tile(pos)

    for pos in game.attack_highlight:
        game._draw_attack_tile(pos)

    game._draw_weapon_swing()
    game._draw_agent()
    game._draw_status_bar()

    pygame.display.flip()
    game.clock.tick(FPS)
