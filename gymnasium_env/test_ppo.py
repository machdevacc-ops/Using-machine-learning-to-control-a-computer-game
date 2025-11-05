from env import GridWorldEnv
from stable_baselines3 import PPO
import torch
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3.common.monitor import Monitor
import time

log_path = "run_log.txt"
"""
dostupne modely pro testovaní:
1. randomized small (k dipsozici i přetrénované s high level - funguje lépe)
model_path = "final_models/ppo_gridworld_random_small_high_level_mlp.zip"
model_path = "final_models/ppo_gridworld_random_small_low_level_mlp.zip"
layout_path = "level_layouts/level_random_small.txt"
2. arena, 5 nepratel, low level akce - identické s prací
model_path = "final_models/ppo_gridworld_arena_low_level_mlp.zip"
layout_path = "level_layouts/level_arena.txt"
3. maze, low level akce - identické s prací
model_path = "final_models/ppo_gridworld_maze_low_level_mlp.zip"
layout_path = "level_layouts/level_maze.txt"
4. randomized big, high_level akce - identické s prací
model_path = "final_models/ppo_gridworld_random_partial_mlp.zip"
layout_path = "level_layouts/level_random_big.txt"

"""
# spusti random big, lze vybrat i jine modely a mapy jak je popsáno výše
model_path = "final_models/ppo_gridworld_random_partial_mlp.zip"
layout_path = "level_layouts/level_random_big.txt"


env = GridWorldEnv(layout_path=layout_path)
env = Monitor(env) 

model = PPO.load(model_path, env=env) 
num_episodes = 50
max_steps = 100
heatmapnotsaved = True  # Set this to False to skip heatmap
rewardTotal = 0

with open(log_path, "w") as log:
    for episode in range(num_episodes):
        print(f"\n Episode {episode + 1}")


        """
        force_furthest - pouzije nejvzdalenejsi 4 starty
        test_emptiness - modifikuje zaplňenost mapy (1 = random tiles budou prázdné, 0 = všechny budou plné)
        use_low_level_actions = True - použije low level akce při testu


        1. rand small high level
        obs, _ = env.reset(force_furthest=False, test_emptiness = 0.2)
        rand small low level
        obs, _ = env.reset(force_furthest=False, test_emptiness = 0.2, use_low_level_actions=True )
        2. arena
        obs, _ = env.reset(force_furthest=False, use_low_level_actions=True)
        3. maze
        obs, _ = env.reset(force_furthest=True, use_low_level_actions=True, omit_step_penalty=True)
        4. random big
        obs, _ = env.reset(force_furthest=False, test_emptiness = 0.2)
        """

        obs, _ = env.reset(force_furthest=False, test_emptiness = 0.2)
        done = False
        steps = 0
        rewardTotal = 0

        while not done:
            env.render()
            time.sleep(0.3) #zpomalení přehrání
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            rewardTotal += reward
            done = terminated or truncated
            steps += 1
            

        # Determine outcome
        result = info.get("result", "unknown")
        if result == "success":
            msg = f"SUCCESS: Reached goal in {steps} steps, reward {rewardTotal}"
        elif result == "u died":
            msg = f"FAIL: Hit too many reset tiles after {steps} steps, reward {rewardTotal}"
        elif result == "stuck_same_tile":
            msg = f"FAIL: Agent stuck in same tile too long, reward {rewardTotal}"
        elif result == "oscillation/loop_stuck":
            msg = f"FAIL: Agent looped in small area, reward {rewardTotal}"
        elif result == "timeout":
            msg = f"TIMEOUT: Reached step limit of {max_steps}, reward {rewardTotal}"
        else:
            msg = f"UNKNOWN result: {result}"

        print(msg)
        log.write(msg + "\n")

        # Generate heatmap only once
        if heatmapnotsaved:
            base_env = env.unwrapped  
            rows, cols = base_env.grid_size
            value_map = np.zeros((rows, cols))

            rows, cols = env.unwrapped.grid_size
            obs_grid = obs.reshape((rows, cols))
            print("Agent observation (as grid):\n", obs_grid)

            for i in range(rows):
                for j in range(cols):
                    test_grid = np.zeros((rows, cols), dtype=np.float32)
                    test_grid[i, j] = 1.0
                    test_obs = test_grid.flatten().reshape(1, -1)
                    test_tensor = torch.tensor(test_obs, dtype=torch.float32).to(model.device)
                    with torch.no_grad():
                        value = model.policy.predict_values(test_tensor).cpu().numpy().item()
                    value_map[i, j] = value

            # Plot heatmap
            plt.figure(figsize=(cols * 0.7, rows * 0.7))
            im = plt.imshow(value_map, cmap='viridis')
            plt.colorbar(im, label='V(s) predicted by agent')
            plt.title("Agent's State-Value Heatmap")

            for i in range(rows):
                for j in range(cols):
                    plt.text(j, i, f"{value_map[i, j]:.2f}", ha='center', va='center', color='white', fontsize=8)

            plt.xticks(np.arange(cols))
            plt.yticks(np.arange(rows))
            plt.grid(False)
            plt.savefig("value_map.png", dpi=150)
            print("Saved value heatmap as value_map.png")
            heatmapnotsaved = False

env.close()
