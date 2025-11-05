from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.env_checker import check_env
from env import GridWorldEnv



check_env(GridWorldEnv(layout_path="level_layouts/level_random_small.txt"), warn=True) #kontrola zdali odpovídá formátu gymnasia


env = GridWorldEnv(layout_path="level_layouts/level_random_small.txt")
#env.use_low_level_actions = True
#env.omit_step_penalty=True #pro trenovani level_maze, vypne penaltu za kroky udílenou na konci
env = Monitor(env)

def linear_schedule(init):
    return lambda progress: progress * init


model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    device="cpu",  # cuda for cnn, cpu for mlp
    tensorboard_log="./ppo_gridworld_tensorboard/" #tensorboard logging
)



model.learn(total_timesteps=400_000)

model.save("final_models/ppo_gridworld_random_small_low_level_mlp")
print("Training complete and model saved.")
