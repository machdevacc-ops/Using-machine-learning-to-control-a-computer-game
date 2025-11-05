import pygame
import random
import os
import numpy as np

from game.config import *
from game.layout_loader import load_layout, save_score
from game.rendering import render_game  

class GridWorldGame:
    def __init__(self, layout_path):
        self.grid = load_layout(layout_path)
        rows, cols = len(self.grid), len(self.grid[0])
        assert all(len(row) == cols for row in self.grid), "Layout must be rectangular"

        self.grid_size = (rows, cols)
        self.outcome = None

        self.window = None
        self.clock = None
        self.font = None
        self.agent_image = None
        self.background_image = None
        self.level_name = os.path.basename(layout_path)

        

        self.step_count = 0
        self.wall_hit_count = 0
        self.hit_reset_count = 0
        self.collected_reward_count = 0
        self.recent_positions = []
        self.DANGER_TILES = []

        #for rubble randomization
        self.rubble_offsets = {} 
        self.rubble_textures_id = {} 
        self.rubble_rotations = {}
        self.rubble_sizes = {}

        #for wall randomization
        self.wall_textures_id = {} 
        self.wall_rotations = {}

        #for trash randomization
        self.trash_offsets = {} 
        self.trash_textures_id = {} 
        self.trash_rotations = {}
        self.trash_sizes = {}

        self.agent_facing = "down"  # initial facing direction

        self.attack_highlight = []

        self._parse_layout()
        self.reset()
        self._init_pygame()

    def _init_pygame(self):
            pygame.init()
            self.window = pygame.display.set_mode((self.grid_size[1] * CELL_SIZE + MARGIN * 2, self.grid_size[0] * CELL_SIZE + MARGIN * 2))
            pygame.display.set_caption("Grid World")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont(None, 40)
            self.poison_frame_order = [0, 1, 2, 3,2,1,0]
            self.poison_frame_index = 0
            self.poison_anim_timer = 0  # time accumulator
            self.poison_frame_duration = 450  # milliseconds per frame
            self._last_poison_tick = pygame.time.get_ticks()
            self.background_color = (0, 0, 0)
            

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

            self.weapon_image = pygame.image.load("game_sprites/characters/character_broom.png").convert_alpha()
            self.weapon_image = pygame.transform.scale(self.weapon_image, (64, 64))  
            self.last_attack_time = 0
            self.attack_display_duration = 250  
            self.agent_move_anim_start = None
            self.agent_move_duration = 250  
            self.enemy_move_animations = {}

           
    def _parse_layout(self):
        self.DMG_TILES = []
        self.REWARD_TILES = []
        self.WALL_TILES = []
        self.RUBBLE_TILES = []
        self.START_POSITIONS = []
        self.ENEMY_POSITIONS = []

        random_tile_targets = ['reset', 'bonus', 'enemy']
        random_weights = [0.2, 0.6, 0.2]
        self.map_emptiness = 0.3

        for r, row in enumerate(self.grid):
            for c, symbol in enumerate(row):
                pos = (r, c)
                tile_type = TILE_SYMBOLS.get(symbol)
                if tile_type == 'random_tile':
                    if random.random() < self.map_emptiness:
                        continue
                    else:
                        chosen_type = chosen_type = random.choices(random_tile_targets, weights=random_weights, k=1)[0]
                        tile_type = chosen_type 


                if tile_type == 'wall':
                    self.WALL_TILES.append(pos)
                elif tile_type == 'start':
                    self.START_POSITIONS.append(pos)
                elif tile_type == 'goal':
                    self.WIN_TILE = pos
                elif tile_type == 'reset':
                    self.DMG_TILES.append(pos)
                elif tile_type == 'bonus':
                    self.REWARD_TILES.append(pos)
                elif tile_type == 'rubble':
                    self.RUBBLE_TILES.append(pos)
                elif tile_type == 'enemy':
                    self.ENEMY_POSITIONS.append(pos)
  
    def reset(self):
        self.step_count = 0
        self.wall_hit_count = 0
        self.wall_hit_streak = 0
        self.collected_reward_count = 0
        self.hit_reset_count = 0
        self.DANGER_TILES.clear()
        self.attack_highlight = []
        self.score = 1000

        self._parse_layout()
        self.initial_reward_tiles_count = len(self.REWARD_TILES)
        self.initial_reset_tile_count = len(self.DMG_TILES)
        self.recent_positions = []

        # rubble randomization
        self.rubble_offsets.clear()
        self.rubble_textures_id.clear()
        self.rubble_rotations.clear()
        self.rubble_weights = [0.4,0.2,0.2,0.1,0.1] #  
        self.rubble_randomization()

        # wall randomization
        self.wall_textures_id.clear()
        self.wall_rotations.clear()
        self.wall_weights = [0.7,0.2,0.1]
        self.wall_randomization()

        # trash/reward randomization
        self.trash_offsets.clear()
        self.trash_textures_id.clear()
        self.trash_rotations.clear()
        self.trash_weights = [0.25,0.25,0.25,0.1,0.1,0.05] #  
        self.trash_randomization()

        print("START_POSITIONS:", self.START_POSITIONS)
        print("WIN_TILE:", getattr(self, "WIN_TILE", None))

        sorted_starts = sorted(
            self.START_POSITIONS,
            key=lambda p: abs(p[0] - self.WIN_TILE[0]) + abs(p[1] - self.WIN_TILE[1]),
            reverse=True
        )
        top_n = 1   
        self.agent_pos = list(random.choice(sorted_starts[:top_n]))

        self.ENEMY_POSITIONS = list(self.ENEMY_POSITIONS)
        self.ENEMY_TARGETS = {}  

        self.enemy_killed = 0




    def wall_randomization(self):
        for tile in self.WALL_TILES: 
            texture_id = random.choices(range(WALL_TYPE_AMOUNT), weights=self.wall_weights, k=1)[0]
            self.wall_textures_id[tile] = texture_id
            self.wall_rotations[tile] = (
                random.choice([True, False]), 
                random.choice([True, False]) 
            )
      

    def rubble_randomization(self):
        for tile in self.RUBBLE_TILES: 
            texture_id = random.choices(range(RUBBLE_TYPE_AMOUNT), weights=self.rubble_weights, k=1)[0]
            self.rubble_textures_id[tile] = texture_id
            self.rubble_rotations[tile] = (
                random.choice([True, False]),  # flip_x
                random.choice([True, False])   # flip_y
            )
        

    def trash_randomization(self):
        for tile in self.REWARD_TILES: 
            texture_id = random.choices(range(TRASH_TYPE_AMOUNT), weights=self.trash_weights, k=1)[0]
            self.trash_textures_id[tile] = texture_id
            self.trash_rotations[tile] = (
                random.choice([True, False]),  # flip_x 
                random.choice([True, False])   # flip_y
            )
            
            base_size = 48
            self.trash_offsets[tile] = (
                random.randint(-10, 10),
                random.randint(-10, 10)
            )
            scale_factor = random.uniform(0.6, 1.2)
            new_size = int(base_size * scale_factor)
            self.trash_sizes[tile] = (new_size, new_size)

    def enemy_step(self):
        
        new_enemy_positions = []

        if self.step_count % 2 == 0:
            self.DANGER_TILES.clear()
            reserved_targets = set()
            self.ENEMY_TARGETS.clear()
            self.enemy_move_animations.clear()


            for pos in self.ENEMY_POSITIONS:
                
                r, c = pos
                neighbors = [
                    (r - 1, c), (r + 1, c),
                    (r, c - 1), (r, c + 1)
                ]
                valid_moves = [
                    n for n in neighbors
                    if 0 <= n[0] < self.grid_size[0] and 0 <= n[1] < self.grid_size[1]
                    and n not in self.WALL_TILES
                    and n not in self.RUBBLE_TILES
                    and n not in reserved_targets
                    and n not in self.ENEMY_POSITIONS 
                    and n not in self.DMG_TILES
                ]
                if valid_moves:
                    
                    next_pos = random.choice(valid_moves)
                    self.ENEMY_TARGETS[pos] = next_pos
                    self.DANGER_TILES.append(next_pos)
                    reserved_targets.add(next_pos)
                else:
                    self.ENEMY_TARGETS[pos] = pos  

        else:
            for old_pos in self.ENEMY_POSITIONS:
                
                next_pos = self.ENEMY_TARGETS.get(old_pos, old_pos)
                if next_pos != old_pos:
                    self.enemy_move_animations[next_pos] = (pygame.time.get_ticks(), 250)  # 180ms duration
                new_enemy_positions.append(next_pos)
            self.ENEMY_POSITIONS = new_enemy_positions
            self.ENEMY_TARGETS.clear()
            self.DANGER_TILES.clear()
 


    def step_from_input(self, key):
        action_map = {
            pygame.K_w: 0,
            pygame.K_s: 1,
            pygame.K_a: 2,
            pygame.K_d: 3,
            pygame.K_SPACE: 4
        }

        if key not in action_map:
            return  

        action = action_map[key]

        self.attack_highlight = []
        self.enemy_step()  
        self.step_count += 1

        rows, cols = self.grid_size
        old_row, old_col = self.agent_pos
        row, col = old_row, old_col
        valid_move = True

        if action == 4:  # ATTACK action
            dir_map = {
                "up": (-1, 0),
                "down": (1, 0),
                "left": (0, -1),
                "right": (0, 1)
            }
            dr, dc = dir_map[self.agent_facing]
            targets = [
                (self.agent_pos[0] + dr, self.agent_pos[1] + dc),
                (self.agent_pos[0] + 2 * dr, self.agent_pos[1] + 2 * dc)
            ]
            for target in targets:
                if target in self.ENEMY_POSITIONS:
                    self.ENEMY_POSITIONS.remove(target)
                    self.enemy_killed += 1
                    self.score += 1000
            self.attack_highlight = targets
            self.last_attack_time = pygame.time.get_ticks()
        else:
            # MOVEMENT action
            if action == 0 and row > 0:
                row -= 1
            elif action == 1 and row < rows - 1:
                row += 1
            elif action == 2 and col > 0:
                col -= 1
            elif action == 3 and col < cols - 1:
                col += 1
            else:
                valid_move = False

            target_pos = (row, col)

            
            if target_pos in self.WALL_TILES + self.RUBBLE_TILES:
                valid_move = False
                row, col = old_row, old_col

            # Move agent
            self.agent_pos = [row, col]

            if valid_move:
                self.agent_move_anim_start = pygame.time.get_ticks()
                self.score -= 100  

                
                if action == 0:
                    self.agent_facing = "up"
                elif action == 1:
                    self.agent_facing = "down"
                elif action == 2:
                    self.agent_facing = "left"
                elif action == 3:
                    self.agent_facing = "right"

       
        if tuple(self.agent_pos) in self.REWARD_TILES:
            self.REWARD_TILES.remove(tuple(self.agent_pos))
            self.collected_reward_count += 1
            self.score += 1100

        

        if tuple(self.agent_pos) in self.ENEMY_POSITIONS:
            self.score -= 10000
            save_score(self.level_name, self.score)
            self.outcome = "killed_by_enemy"
            return

        if tuple(self.agent_pos) in self.DMG_TILES:
            self.score -= 10000
            save_score(self.level_name, self.score)
            self.outcome = "stepped_on_poison"
            return

        if tuple(self.agent_pos) == self.WIN_TILE:
            self.score += 10000 + self.collected_reward_count + self.enemy_killed * 1000
            save_score(self.level_name, self.score)
            self.outcome = "victory"
            return
   

    def render(self):
        render_game(self)

            

    def _draw_weapon_swing(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.last_attack_time
        if elapsed > self.attack_display_duration:
            return 

        progress = elapsed / self.attack_display_duration 

        
        fade_in_out = (1 - abs(2 * progress - 1))  # peak at progress=0.5
        alpha = int(255 * fade_in_out)

        
        swing_arc_angle = 60  # total arc rotation
        swing_distance = 50  # pixel movement forward
        swing_lift = 20       # pixel lift at the beginning

        # Direction and rotation base
        angle_map = {
            "up": 0,
            "down": 180,
            "left": 90,
            "right": -90
        }
        drc_map = {
            "up": (-1, 0),
            "down": (1, 0),
            "left": (0, -1),
            "right": (0, 1)
        }

        base_angle = angle_map[self.agent_facing]
        arc_offset = -swing_arc_angle * (progress - 0.5)  # swing arc centered
        swing_angle = base_angle + arc_offset

        # Forward + lift movement
        dr, dc = drc_map[self.agent_facing]
        forward_offset = swing_distance * progress
        lift_offset = -swing_lift * (1 - (2 * (progress - 0.5)) ** 2)  # bell curve

        # Center position in front of agent
        center_x = MARGIN + (self.agent_pos[1] + dc) * CELL_SIZE + CELL_SIZE // 2
        center_y = MARGIN + (self.agent_pos[0] + dr) * CELL_SIZE + CELL_SIZE // 2

        offset_x = int(dc * forward_offset - dr * lift_offset)
        offset_y = int(dr * forward_offset + dc * lift_offset)

        # Scaling for punch effect
        scale = 1.0 + 0.25 * fade_in_out

        # Apply transforms
        weapon = pygame.transform.rotozoom(self.weapon_image, swing_angle, scale)
        weapon.set_alpha(alpha)
        rect = weapon.get_rect(center=(center_x + offset_x, center_y + offset_y))

        self.window.blit(weapon, rect.topleft)



    def _draw_status_bar(self):
        # Draw steps
        step_text = self.font.render(f"Steps: {self.step_count}", True, (255, 255, 255))
        self.window.blit(step_text, (MARGIN, 20))

        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 0))
        text_rect = score_text.get_rect()
        text_rect.topright = (self.window.get_width() - MARGIN, 20)
        self.window.blit(score_text, text_rect)

    def _draw_danger_tile(self, pos):
        x = MARGIN + pos[1] * CELL_SIZE
        y = MARGIN + pos[0] * CELL_SIZE
        danger_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

       
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        surface.fill((255, 0, 0, 100))  
        self.window.blit(surface, (x, y))

        
        pygame.draw.rect(self.window, (255, 0, 0), danger_rect, 3)

    def _draw_attack_tile(self, pos):
        x = MARGIN + pos[1] * CELL_SIZE
        y = MARGIN + pos[0] * CELL_SIZE

        
        surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)

        
        outline_color = (255, 255, 255, 150)  # RGBA
        border_width = 3  

        pygame.draw.rect(surface, outline_color, surface.get_rect(), border_width)

        
        self.window.blit(surface, (x, y))


    def _draw_enemy(self, pos):
        base_x = MARGIN + pos[1] * CELL_SIZE
        base_y = MARGIN + pos[0] * CELL_SIZE
        sprite = self.enemy_image

        now = pygame.time.get_ticks()
        if pos in self.enemy_move_animations:
            start_time, duration = self.enemy_move_animations[pos]
            elapsed = now - start_time
            if elapsed < duration:
                progress = elapsed / duration
                scale = 1.2 - 0.2 * progress  # grows then shrinks
                min_alpha = 150  
                alpha_range = 255 - min_alpha
                alpha = int(min_alpha + alpha_range * (1 - abs(progress - 0.5) * 2))
                sprite = pygame.transform.rotozoom(sprite, 0, scale)
                sprite.set_alpha(alpha)
            else:
                del self.enemy_move_animations[pos]  

        rect = sprite.get_rect(center=(base_x + CELL_SIZE // 2, base_y + CELL_SIZE // 2))
        self.window.blit(sprite, rect.topleft)



    def _draw_target_tile(self,pos):
        x = MARGIN + pos[1] * CELL_SIZE
        y = MARGIN + pos[0] * CELL_SIZE
        self.window.blit(self.target_image, (x, y))

    def _draw_base_tiles(self):
        rows, cols = self.grid_size
        for r in range(rows):
            for c in range(cols):
                x = MARGIN + c * CELL_SIZE
                y = MARGIN + r * CELL_SIZE
                tile_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.window, TILE_BASE_COLOR, tile_rect)


    def _draw_trash(self, pos):
        base_x = MARGIN + pos[1] * CELL_SIZE
        base_y = MARGIN + pos[0] * CELL_SIZE

        texture_id = self.trash_textures_id.get(pos)
        if texture_id is None:
            return

        texture = self.trash_images[texture_id]
        img_rect = texture.get_rect()

        size = self.trash_sizes.get(pos, (64, 64))
        texture = pygame.transform.smoothscale(texture, size)
        center_x = base_x + (CELL_SIZE - img_rect.width) // 2
        center_y = base_y + (CELL_SIZE - img_rect.height) // 2

        offset_x, offset_y = self.trash_offsets.get(pos, (0, 0))
        final_x = center_x + offset_x
        final_y = center_y + offset_y

        flip_x, flip_y = self.trash_rotations.get(pos, (False, False))

        texture = pygame.transform.flip(texture, flip_x, flip_y)

        self.window.blit(texture, (final_x, final_y))


    def _draw_poison(self, pos):
        base_x = MARGIN + pos[1] * CELL_SIZE
        base_y = MARGIN + pos[0] * CELL_SIZE

        # Wobble & scale animation
        t = pygame.time.get_ticks() / 1000
        offset_x = int(2 * np.sin(t + pos[0]))
        offset_y = int(8 * np.cos(t + pos[1]))
        scale_factor = 1.0 + 0.2 * np.sin(t * 2 + pos[0] + pos[1])

        
        frame_id = self.poison_frame_order[self.poison_frame_index]
        frame = self.poison_frames[frame_id]

        
        original_size = frame.get_size()
        new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
        frame = pygame.transform.smoothscale(frame, new_size)

       
        draw_x = base_x + (CELL_SIZE - new_size[0]) // 2 + offset_x
        draw_y = base_y + (CELL_SIZE - new_size[1]) // 2 + offset_y

        self.window.blit(frame, (draw_x, draw_y))



    def _draw_rubble(self, pos):
        base_x = MARGIN + pos[1] * CELL_SIZE
        base_y = MARGIN + pos[0] * CELL_SIZE

        texture_id = self.rubble_textures_id.get(pos)
        if texture_id is None:
            return

        texture = self.rubble_images[texture_id]
        img_rect = texture.get_rect()

        size = self.rubble_sizes.get(pos, (64, 64))

        

        center_x = base_x + (CELL_SIZE - img_rect.width) // 2
        center_y = base_y + (CELL_SIZE - img_rect.height) // 2


        flip_x, flip_y = self.rubble_rotations.get(pos, (False, False))

        texture = pygame.transform.flip(texture, flip_x, flip_y)

        self.window.blit(texture, (center_x, center_y))



    def _draw_grid(self):
        rows, cols = self.grid_size
        for i in range(cols + 1):
            x = MARGIN + i * CELL_SIZE
            pygame.draw.line(
                self.window,
                GRID_LINE_COLOR,
                (x, MARGIN),
                (x, MARGIN + rows * CELL_SIZE),
                GRID_LINE_WIDTH
            )
        for i in range(rows + 1):
            y = MARGIN + i * CELL_SIZE
            pygame.draw.line(
                self.window,
                GRID_LINE_COLOR,
                (MARGIN, y),
                (MARGIN + cols * CELL_SIZE, y),
                GRID_LINE_WIDTH
            )
        


    def _draw_tile(self, pos, color):
        x = MARGIN + pos[1] * CELL_SIZE
        y = MARGIN + pos[0] * CELL_SIZE
        tile_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(self.window, color, tile_rect)


    def _draw_wall(self,pos):
        base_x = MARGIN + pos[1] * CELL_SIZE
        base_y = MARGIN + pos[0] * CELL_SIZE

        texture_id = self.wall_textures_id.get(pos)
        if texture_id is None:
            return

        texture = self.wall_images[texture_id]
        img_rect = texture.get_rect()

        center_x = base_x + (CELL_SIZE - img_rect.width) // 2
        center_y = base_y + (CELL_SIZE - img_rect.height) // 2

        flip_x, flip_y = self.wall_rotations.get(pos, (False, False))

        texture = pygame.transform.flip(texture, flip_x, flip_y)

        self.window.blit(texture, (center_x, center_y))

    def _draw_agent(self):
        
        scale = 1.0
        alpha = 255

        # Animate if moving
        if self.agent_move_anim_start is not None:
            now = pygame.time.get_ticks()
            elapsed = now - self.agent_move_anim_start
            progress = elapsed / self.agent_move_duration

            if progress >= 1.0:
                self.agent_move_anim_start = None 
            else:
                scale = 0.9 + 0.2 * abs(0.5 - progress) * 2  # shrink and grow
                alpha = int(150 + 105 * progress) if progress < 0.5 else int(255 - 105 * (progress - 0.5) * 2)

        
        sprite = self.agent_image

        if self.agent_facing == "down":
            angle = 0
        elif self.agent_facing == "left":
            angle = -90
        elif self.agent_facing == "up":
            angle = 180
        elif self.agent_facing == "right":
            angle = 90
        else:
            angle = 0

        sprite = pygame.transform.rotate(sprite, angle)

        
        original_size = sprite.get_size()
        new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
        sprite = pygame.transform.smoothscale(sprite, new_size)

        sprite.set_alpha(alpha)

        
        rect = sprite.get_rect()
        x = MARGIN + self.agent_pos[1] * CELL_SIZE + (CELL_SIZE - rect.width) // 2
        y = MARGIN + self.agent_pos[0] * CELL_SIZE + (CELL_SIZE - rect.height) // 2

        self.window.blit(sprite, (x, y))