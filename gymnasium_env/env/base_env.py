from gymnasium import Env, spaces
import numpy as np
import random
from collections import deque

from config import FPS, RUBBLE_TYPE_AMOUNT, WALL_TYPE_AMOUNT, TRASH_TYPE_AMOUNT
from .layout_loader import load_layout, get_tile_type, parse_layout
from .rendering import GridWorldRenderer



class GridWorldEnv(Env):
    metadata = {"render_modes": ["human"], "render_fps": FPS}

    def __init__(self, layout_path):
        super().__init__()

        self.grid = load_layout(layout_path)
        rows, cols = len(self.grid), len(self.grid[0])
        assert all(len(row) == cols for row in self.grid), "Layout must be rectangular"
        self.grid_size = (rows, cols)

        # spaces discrete 5 (5 actions)
        self.action_space = spaces.Discrete(5)
        self.observation_space = spaces.Box(
            low=0.0,
            high=8.0, #8 types of objects as shown in get_obs
            shape=(rows * cols,),
            dtype=np.float32
        )

        # Rendering engine
        self.renderer = GridWorldRenderer(self)

        # Game state
        self.step_count = 0
        self.wall_hit_count = 0
        self.hit_reset_count = 0
        self.collected_reward_count = 0
        self.recent_positions = []
        self.DANGER_TILES = []

        # Randomization state
        self.rubble_offsets = {} 
        self.rubble_textures_id = {} 
        self.rubble_rotations = {}
        self.rubble_sizes = {}

        self.wall_textures_id = {} 
        self.wall_rotations = {}

        self.trash_offsets = {} 
        self.trash_textures_id = {} 
        self.trash_rotations = {}
        self.trash_sizes = {}

        self.agent_facing = "down"

        self.curriculum_level = 0
        self.episode_successes = 0
        self.penalized_danger_tiles = set()
        self.map_emptiness = 0.8

        self.attack_highlight = []
        self.use_low_level_actions = False
        self.default_omit_step_penalty = False
        self._load_layout_state()

    def _load_layout_state(self):
        layout_data = parse_layout(self.grid, self.episode_successes, self.map_emptiness)

        self.WALL_TILES = layout_data["WALL_TILES"]
        self.START_POSITIONS = layout_data["START_POSITIONS"]
        self.WIN_TILE = layout_data["WIN_TILE"]
        self.DMG_TILES = layout_data["DMG_TILES"]
        self.REWARD_TILES = layout_data["REWARD_TILES"]
        self.RUBBLE_TILES = layout_data["RUBBLE_TILES"]
        self.ENEMY_POSITIONS = layout_data["ENEMY_POSITIONS"]
        self.map_emptiness = layout_data["map_emptiness"]

            
    def _get_obs(self):
        rows, cols = self.grid_size
        grid = np.zeros((rows, cols), dtype=np.float32)

        for r in range(rows):
            for c in range(cols):
                pos = (r, c)
                if pos == tuple(self.agent_pos):
                    grid[r, c] = 1.0  # agent
                elif pos == self.WIN_TILE:
                    grid[r, c] = 2.0  # goal
                elif pos in self.DMG_TILES:
                    grid[r, c] = 3.0  # reset
                elif pos in self.REWARD_TILES:
                    grid[r, c] = 4.0  # bonus
                elif pos in self.WALL_TILES:
                    grid[r, c] = 5.0  # wall
                elif pos in self.RUBBLE_TILES:
                    grid[r, c] = 6.0  # rubble
                elif pos in self.ENEMY_POSITIONS:
                    grid[r, c] = 7.0  # enemy
                elif pos in self.DANGER_TILES:
                    grid[r, c] = 8.0  # dmg incoming
                else:
                    grid[r, c] = 0.0  # empty

        return grid.flatten()
    
    #function params used for testing/training modifications
    def reset(self, seed=None, force_furthest=False, test_emptiness=None, use_low_level_actions=None, omit_step_penalty=None):
        self.step_count = 0
        self.wall_hit_count = 0
        self.wall_hit_streak = 0
        self.collected_reward_count = 0
        self.hit_reset_count = 0
        self.enemy_killed = 0
        self.DANGER_TILES.clear()
        self.attack_highlight = []
        self.recent_positions = []

        if use_low_level_actions is not None:
            self.use_low_level_actions = use_low_level_actions

        self.omit_step_penalty = omit_step_penalty if omit_step_penalty is not None else self.default_omit_step_penalty

        self._load_layout_state()

        self.initial_reward_tiles_count = len(self.REWARD_TILES)
        self.initial_reset_tile_count = len(self.DMG_TILES)

        # RUBBLE randomization
        self.rubble_offsets.clear()
        self.rubble_textures_id.clear()
        self.rubble_rotations.clear()
        self.rubble_weights = [0.4, 0.2, 0.2, 0.1, 0.1]
        self.rubble_randomization()

        # WALL randomization
        self.wall_textures_id.clear()
        self.wall_rotations.clear()
        self.wall_weights = [0.7, 0.2, 0.1]
        self.wall_randomization()

        # TRASH (reward) randomization
        self.trash_offsets.clear()
        self.trash_textures_id.clear()
        self.trash_rotations.clear()
        self.trash_weights = [0.25, 0.25, 0.25, 0.1, 0.1, 0.05]
        self.trash_randomization()

        # Agent spawn logic 
        sorted_starts = sorted(
            self.START_POSITIONS,
            key=lambda p: abs(p[0] - self.WIN_TILE[0]) + abs(p[1] - self.WIN_TILE[1]),
            reverse=False  
        )

        if force_furthest:
            top_n = min(4, len(sorted_starts))
            self.agent_pos = list(random.choice(sorted_starts[-top_n:]))  #pick 4 furthest
        elif self.curriculum_level >= len(self.START_POSITIONS) - 1:
            top_n = min(4, len(sorted_starts))
            self.agent_pos = list(random.choice(sorted_starts[-top_n:])) 
        else:
            max_index = min(self.curriculum_level, len(sorted_starts) - 1)
            self.agent_pos = list(sorted_starts[max_index])  # curriculum: closer → further


        # Manual override for map emptiness
        if test_emptiness is not None:
            self.map_emptiness = test_emptiness

        self.ENEMY_POSITIONS = list(self.ENEMY_POSITIONS)
        self.ENEMY_TARGETS = {}

        return self._get_obs(), {}

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
                random.choice([True, False]),
                random.choice([True, False])
            )

    def trash_randomization(self):
        for tile in self.REWARD_TILES:
            texture_id = random.choices(range(TRASH_TYPE_AMOUNT), weights=self.trash_weights, k=1)[0]
            self.trash_textures_id[tile] = texture_id
            self.trash_rotations[tile] = (
                random.choice([True, False]),
                random.choice([True, False])
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
        #wont move into most objects and other enemies
        new_enemy_positions = []

        if self.step_count % 2 == 0:
            self.DANGER_TILES.clear()
            reserved_targets = set()
            self.ENEMY_TARGETS.clear()

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
                    self.ENEMY_TARGETS[pos] = pos  # no move

        else:
            for old_pos in self.ENEMY_POSITIONS:
                next_pos = self.ENEMY_TARGETS.get(old_pos, old_pos)
                new_enemy_positions.append(next_pos)
            self.ENEMY_POSITIONS = new_enemy_positions
            self.ENEMY_TARGETS.clear()
            self.DANGER_TILES.clear()

    def _fallback_move(self, reason):
        #Try moving to safe tile, then try any valid direction that is not blocked.

        direction = self._get_safe_direction()
        if direction is not None:
            return self._step_low_level(direction)

        possible_dirs = [0, 1, 2, 3]
        row, col = self.agent_pos
        candidates = {
            0: (row - 1, col),  # up
            1: (row + 1, col),  # down
            2: (row, col - 1),  # left
            3: (row, col + 1)   # right
        }

        for d in possible_dirs:
            target = candidates[d]
            if (0 <= target[0] < self.grid_size[0] and
                0 <= target[1] < self.grid_size[1] and
                target not in self.WALL_TILES and
                target not in self.RUBBLE_TILES):
                return self._step_low_level(d)

        return self._get_obs(), -1, True, False, {"result": reason + "_stuck"}

    def step(self, action): 

        if self.use_low_level_actions:
            return self._step_low_level(action)

        if action == 0:  # MOVE_TO_GOAL
            direction = self._get_direction_to_target(self.WIN_TILE)
            if direction is not None:
                return self._step_low_level(direction)
            else:
                return self._fallback_move("no_path_to_goal")

        elif action == 1:  # MOVE_TO_REWARD
            direction = self._get_direction_to_target(self.REWARD_TILES)
            if direction is not None:
                return self._step_low_level(direction)
            else:
                direction = self._get_direction_to_target(self.WIN_TILE)
                if direction is not None:
                    return self._step_low_level(direction)
                else:
                    return self._fallback_move("no_rewards")

        elif action == 2:  # MOVE_TO_SAFE_TILE
            direction = self._get_safe_direction()
            if direction is not None:
                return self._step_low_level(direction)
            else:
                return self._fallback_move("no_safe_moves")

        elif action == 3:  # ATTACK
            low_action = 4

        elif action == 4:  # MOVE_TO_ENEMY
            direction = self._get_direction_to_target(self.ENEMY_POSITIONS)
            if direction is not None:
                return self._step_low_level(direction)
            else:
                direction = self._get_direction_to_target(self.WIN_TILE)
                if direction is not None:
                    return self._step_low_level(direction)
                else:
                    return self._fallback_move("no_enemies")
        else:
            low_action = random.choice([0, 1, 2, 3])

        return self._step_low_level(low_action)
    
    def _get_safe_direction(self):
        #Choose a safe direction from current position
        row, col = self.agent_pos
        directions = [
            (-1, 0),  # up
            (1, 0),   # down
            (0, -1),  # left
            (0, 1)    # right
        ]

        safe_moves = []
        for idx, (dr, dc) in enumerate(directions):
            nr, nc = row + dr, col + dc
            pos = (nr, nc)
            if (
                0 <= nr < self.grid_size[0]
                and 0 <= nc < self.grid_size[1]
                and pos not in self.WALL_TILES
                and pos not in self.RUBBLE_TILES
                and pos not in self.DMG_TILES
                and pos not in self.DANGER_TILES
                and pos not in self.ENEMY_POSITIONS
            ):
                safe_moves.append((idx, pos))

        if not safe_moves:
            return None

        return random.choice(safe_moves)[0]
    
    def _get_direction_to_target(self, targets):
        if not isinstance(targets, list):
            targets = [targets]

        rows, cols = self.grid_size
        visited = set()
        queue = deque()
        came_from = {}

        start = tuple(self.agent_pos)
        queue.append(start)
        visited.add(start)

        blocked = set(self.WALL_TILES + self.RUBBLE_TILES + self.DMG_TILES)
        found_target = None

        while queue:
            current = queue.popleft()
            if current in targets:
                found_target = current
                break
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = current[0] + dr, current[1] + dc
                neighbor = (nr, nc)
                if (0 <= nr < rows and 0 <= nc < cols and
                    neighbor not in visited and
                    neighbor not in blocked):
                    queue.append(neighbor)
                    visited.add(neighbor)
                    came_from[neighbor] = current

        if found_target is None:
            return None

        step = found_target
        while came_from.get(step) != start:
            step = came_from[step]

        dir_map = {
            (-1, 0): 0,  # up
            (1, 0): 1,   # down
            (0, -1): 2,  # left
            (0, 1): 3    # right
        }
        dr = step[0] - start[0]
        dc = step[1] - start[1]
        return dir_map.get((dr, dc))

    def _step_low_level(self, action):
        self.attack_highlight = []
        self.enemy_step()
        self.step_count += 1
        rows, cols = self.grid_size
        old_row, old_col = self.agent_pos
        row, col = old_row, old_col
        valid_move = True
        info = {}
        terminated = False
        truncated = False
        attack_perfomed = False
        reward = 0

        if action == 4:  # attack action
            dir_map = {
                "up": (-1, 0),
                "down": (1, 0),
                "left": (0, -1),
                "right": (0, 1)
            }
            dr, dc = dir_map[self.agent_facing]
            hit_enemy = False
            targets = [
                (self.agent_pos[0] + dr, self.agent_pos[1] + dc),
                (self.agent_pos[0] + 2 * dr, self.agent_pos[1] + 2 * dc)
            ]
            for target in targets:
                if target in self.ENEMY_POSITIONS:
                    self.ENEMY_POSITIONS.remove(target)
                    hit_enemy = True
                    self.enemy_killed += 1
                    reward += 0.1
            if hit_enemy:
                info["result"] = "enemy_killed"
            self.attack_highlight = targets
            attack_perfomed = True

        if not attack_perfomed:
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

            self.agent_pos = [row, col]

            if valid_move:
                if action == 0:
                    self.agent_facing = "up"
                elif action == 1:
                    self.agent_facing = "down"
                elif action == 2:
                    self.agent_facing = "left"
                elif action == 3:
                    self.agent_facing = "right"
            else:
                self.wall_hit_count += 1
                self.wall_hit_streak += 1
                #Checks if agent is running into walls
                if self.wall_hit_streak >= 10:
                    truncated = True
                    reward -= 1
                    info["result"] = "stuck_same_tile"
                    return self._get_obs(), reward, terminated, truncated, info
            if valid_move:
                self.wall_hit_streak = 0

            # Loop/oscillation detection
            self.recent_positions.append(tuple(self.agent_pos))
            if len(self.recent_positions) > 30:
                self.recent_positions.pop(0)

            if len(self.recent_positions) >= 30:
                recent = self.recent_positions[-30:]
                unique_positions = set(recent)
                if len(unique_positions) <= 4:
                    reward = -1
                    truncated = True
                    info["result"] = "oscillation/loop_stuck"
                    return self._get_obs(), reward, terminated, truncated, info

        # Collision with reward
        if tuple(self.agent_pos) in self.REWARD_TILES:
            reward += 0.1
            self.REWARD_TILES.remove(tuple(self.agent_pos))
            self.collected_reward_count += 1

        # Collision with enemy
        if tuple(self.agent_pos) in self.ENEMY_POSITIONS:
            reward -= 1
            terminated = True
            info["result"] = "u died"
            return self._get_obs(), reward, terminated, truncated, info

        # Collision with reset tile (poison)
        if tuple(self.agent_pos) in self.DMG_TILES:
            self.DMG_TILES.remove(tuple(self.agent_pos))
            self.hit_reset_count += 1
            if self.hit_reset_count >= 1:
                reward -= 1
                terminated = True
                info["result"] = "u died"
                return self._get_obs(), reward, terminated, truncated, info

        # Win condition
        if tuple(self.agent_pos) == self.WIN_TILE:
            reward = 1 + self.collected_reward_count + self.enemy_killed
            if not self.omit_step_penalty:
                reward -= 0.01 * self.step_count

            terminated = True
            info["result"] = "success"
            self.episode_successes += 1
            if self.episode_successes >= 5:
                self.curriculum_level += 1
                self.episode_successes = 0
                print(self.curriculum_level)
            return self._get_obs(), reward, terminated, truncated, info

        # Timeout
        if self.step_count >= 150 and not terminated:
            reward -= 1
            truncated = True
            info["result"] = "timeout"
            return self._get_obs(), reward, terminated, truncated, info

        return self._get_obs(), reward, terminated, truncated, info

    
    def render(self, mode="human"):
        self.renderer.render()

    def close(self):
        self.renderer.close()







