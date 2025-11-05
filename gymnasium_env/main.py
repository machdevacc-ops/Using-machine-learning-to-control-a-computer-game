import pygame
from env import GridWorldEnv
#uses randomized actions, for testing use test_ppo.py
def main():
    layout_path = "level_layouts/level_random_big.txt"
    env = GridWorldEnv(layout_path)

    obs, _ = env.reset()  
    done = False

    while True:
        env.render()  

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                env.close()
                return

        # Take random action
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated or truncated:
            print("Episode ended:", info.get("result", "unknown"))
            obs, _ = env.reset()

if __name__ == "__main__":
    main()
