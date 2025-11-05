import pygame
import numpy as np
from config import (
    CELL_SIZE, AGENT_WIDTH, AGENT_HEIGHT, MARGIN, FPS,
    TILE_BASE_COLOR, GRID_LINE_COLOR, GRID_LINE_WIDTH
)

class GridWorldRenderer:
    def __init__(self, env):
        self.env = env
        self.window = None
        self.clock = None
        self.font = None

        # Animation
        self.poison_frame_order = [0, 1, 2, 3, 2, 1, 0]
        self.poison_frame_index = 0
        self.poison_frame_duration = 450  # ms
        self._last_poison_tick = 0

    def render(self):
        rows, cols = self.env.grid_size
        window_width = cols * CELL_SIZE + MARGIN * 2
        window_height = rows * CELL_SIZE + MARGIN * 2

        if self.window is None:
            pygame.init()
            self.window = pygame.display.set_mode((window_width, window_height))
            pygame.display.set_caption("Grid World")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont(None, 40)

            
            self._load_images(window_width, window_height)

        # Animation frame update
        now = pygame.time.get_ticks()
        if now - self._last_poison_tick > self.poison_frame_duration:
            self.poison_frame_index = (self.poison_frame_index + 1) % len(self.poison_frame_order)
            self._last_poison_tick = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        self.window.fill((0, 0, 0))
        self._draw_base_tiles()
        self._draw_grid()

        for tile in self.env.DMG_TILES:
            self._draw_poison(tile)

        for tile in self.env.REWARD_TILES:
            self._draw_trash(tile)

        self._draw_target_tile(self.env.WIN_TILE)

        for tile in self.env.WALL_TILES:
            self._draw_wall(tile)

        for tile in self.env.RUBBLE_TILES:
            self._draw_rubble(tile)

        for pos in self.env.ENEMY_POSITIONS:
            self._draw_enemy(pos)

        for pos in self.env.DANGER_TILES:
            self._draw_danger_tile(pos)

        for pos in self.env.attack_highlight:
            self._draw_attack_tile(pos)

        self._draw_agent()
        self._draw_step_count()
        pygame.display.flip()
        self.clock.tick(FPS)

    def _load_images(self, window_width, window_height):
        
        self.agent_image = pygame.image.load("game_sprites/characters/character_main_still.png").convert_alpha()
        self.agent_image = pygame.transform.scale(self.agent_image, (AGENT_WIDTH, AGENT_HEIGHT))

        self.enemy_image = pygame.image.load("game_sprites/characters/character_enemy.png").convert_alpha()
        self.enemy_image = pygame.transform.scale(self.enemy_image, (64, 64))

        self.rubble_images = [
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/rubble_rocks.png").convert_alpha(), (64, 64)),
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/rubble_stone.png").convert_alpha(), (64, 64)),
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/rubble_debris.png").convert_alpha(), (64, 64)),
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/rubble_barrel.png").convert_alpha(), (64, 64)),
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/rubble_crate.png").convert_alpha(), (64, 64))
        ]

        self.wall_images = [
            pygame.transform.scale(pygame.image.load("game_sprites/walls/wall_solid.png").convert_alpha(), (64, 64)),
            pygame.transform.scale(pygame.image.load("game_sprites/walls/wall_cracked.png").convert_alpha(), (64, 64)),
            pygame.transform.scale(pygame.image.load("game_sprites/walls/wall_destroyed.png").convert_alpha(), (64, 64))
        ]

        self.poison_frames = [
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/poison/poison_1.png").convert_alpha(), (64, 64)),
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/poison/poison_2.png").convert_alpha(), (64, 64)),
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/poison/poison_3.png").convert_alpha(), (64, 64)),
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/poison/poison_4.png").convert_alpha(), (64, 64))
        ]

        self.trash_images = [
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/trash/trash_food.png").convert_alpha(), (48, 48)),
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/trash/trash_slime.png").convert_alpha(), (48, 48)),
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/trash/trash_cobweb.png").convert_alpha(), (48, 48)),
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/trash/trash_skulls.png").convert_alpha(), (48, 48)),
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/trash/trash_gold.png").convert_alpha(), (48, 48)),
            pygame.transform.scale(pygame.image.load("game_sprites/enviroment/trash/trash_chair.png").convert_alpha(), (48, 48))
        ]

        self.target_image = pygame.image.load("game_sprites/enviroment/staircase_steps.png").convert_alpha()
        self.target_image = pygame.transform.scale(self.target_image, (64, 64))

    def _draw_base_tiles(self):
        rows, cols = self.env.grid_size
        for r in range(rows):
            for c in range(cols):
                x = MARGIN + c * CELL_SIZE
                y = MARGIN + r * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.window, TILE_BASE_COLOR, rect)

    def _draw_grid(self):
        rows, cols = self.env.grid_size
        for i in range(cols + 1):
            x = MARGIN + i * CELL_SIZE
            pygame.draw.line(self.window, GRID_LINE_COLOR, (x, MARGIN), (x, MARGIN + rows * CELL_SIZE), GRID_LINE_WIDTH)
        for i in range(rows + 1):
            y = MARGIN + i * CELL_SIZE
            pygame.draw.line(self.window, GRID_LINE_COLOR, (MARGIN, y), (MARGIN + cols * CELL_SIZE, y), GRID_LINE_WIDTH)

    def _draw_wall(self, pos):
        x = MARGIN + pos[1] * CELL_SIZE
        y = MARGIN + pos[0] * CELL_SIZE
        texture_id = self.env.wall_textures_id.get(pos)
        if texture_id is None:
            return
        texture = self.wall_images[texture_id]
        flip_x, flip_y = self.env.wall_rotations.get(pos, (False, False))
        texture = pygame.transform.flip(texture, flip_x, flip_y)
        self.window.blit(texture, (x, y))

    def _draw_rubble(self, pos):
        x = MARGIN + pos[1] * CELL_SIZE
        y = MARGIN + pos[0] * CELL_SIZE
        texture_id = self.env.rubble_textures_id.get(pos)
        if texture_id is None:
            return
        texture = self.rubble_images[texture_id]
        flip_x, flip_y = self.env.rubble_rotations.get(pos, (False, False))
        texture = pygame.transform.flip(texture, flip_x, flip_y)
        self.window.blit(texture, (x, y))

    def _draw_trash(self, pos):
        base_x = MARGIN + pos[1] * CELL_SIZE
        base_y = MARGIN + pos[0] * CELL_SIZE
        texture_id = self.env.trash_textures_id.get(pos)
        if texture_id is None:
            return
        texture = self.trash_images[texture_id]
        size = self.env.trash_sizes.get(pos, (48, 48))
        texture = pygame.transform.smoothscale(texture, size)
        offset_x, offset_y = self.env.trash_offsets.get(pos, (0, 0))
        flip_x, flip_y = self.env.trash_rotations.get(pos, (False, False))
        texture = pygame.transform.flip(texture, flip_x, flip_y)
        center_x = base_x + (CELL_SIZE - size[0]) // 2 + offset_x
        center_y = base_y + (CELL_SIZE - size[1]) // 2 + offset_y
        self.window.blit(texture, (center_x, center_y))

    def _draw_poison(self, pos):
        base_x = MARGIN + pos[1] * CELL_SIZE
        base_y = MARGIN + pos[0] * CELL_SIZE
        t = pygame.time.get_ticks() / 1000
        offset_x = int(2 * np.sin(t + pos[0]))
        offset_y = int(8 * np.cos(t + pos[1]))
        scale = 1.0 + 0.2 * np.sin(t * 2 + pos[0] + pos[1])
        frame_id = self.poison_frame_order[self.poison_frame_index]
        frame = self.poison_frames[frame_id]
        new_size = (int(frame.get_width() * scale), int(frame.get_height() * scale))
        frame = pygame.transform.smoothscale(frame, new_size)
        draw_x = base_x + (CELL_SIZE - new_size[0]) // 2 + offset_x
        draw_y = base_y + (CELL_SIZE - new_size[1]) // 2 + offset_y
        self.window.blit(frame, (draw_x, draw_y))

    def _draw_target_tile(self, pos):
        x = MARGIN + pos[1] * CELL_SIZE
        y = MARGIN + pos[0] * CELL_SIZE
        self.window.blit(self.target_image, (x, y))

    def _draw_enemy(self, pos):
        x = MARGIN + pos[1] * CELL_SIZE
        y = MARGIN + pos[0] * CELL_SIZE
        self.window.blit(self.enemy_image, (x, y))

    def _draw_agent(self):
        sprite = self.agent_image
        direction = self.env.agent_facing
        if direction == "up":
            angle = 180
        elif direction == "down":
            angle = 0
        elif direction == "left":
            angle = -90
        elif direction == "right":
            angle = 90
        else:
            angle = 0
        sprite = pygame.transform.rotate(sprite, angle)
        rect = sprite.get_rect()
        x = MARGIN + self.env.agent_pos[1] * CELL_SIZE + (CELL_SIZE - rect.width) // 2
        y = MARGIN + self.env.agent_pos[0] * CELL_SIZE + (CELL_SIZE - rect.height) // 2
        self.window.blit(sprite, (x, y))

    def _draw_step_count(self):
        text = self.font.render(f"Steps: {self.env.step_count}", True, (255, 255, 255))
        self.window.blit(text, (MARGIN, 20))

    def _draw_danger_tile(self, pos):
        x = MARGIN + pos[1] * CELL_SIZE
        y = MARGIN + pos[0] * CELL_SIZE
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        surface.fill((255, 0, 0, 100))
        self.window.blit(surface, (x, y))
        pygame.draw.rect(self.window, (255, 0, 0), (x, y, CELL_SIZE, CELL_SIZE), 3)

    def _draw_attack_tile(self, pos):
        x = MARGIN + pos[1] * CELL_SIZE
        y = MARGIN + pos[0] * CELL_SIZE
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(surface, (255, 255, 255, 150), surface.get_rect(), 3)
        self.window.blit(surface, (x, y))

    def close(self):
        if self.window:
            pygame.quit()
            self.window = None
