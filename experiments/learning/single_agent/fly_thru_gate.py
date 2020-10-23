import time
import argparse
import gym
from stable_baselines3 import A2C
from stable_baselines3.a2c import MlpPolicy
from stable_baselines3.common.env_checker import check_env
import ray
from ray.tune import register_env
from ray.rllib.agents import ppo

from gym_pybullet_drones.envs.single_agent_rl.FlyThruGateAviary import FlyThruGateAviary
from gym_pybullet_drones.utils.utils import *


if __name__ == "__main__":

    #### Define and parse (optional) arguments for the script ##########################################
    parser = argparse.ArgumentParser(description='Single agent reinforcement learning example script using FlyThruGateAviary')
    parser.add_argument('--rllib',      default=False,        type=str2bool,       help='Whether to use RLlib PPO in place of stable-baselines A2C (default: False)', metavar='')
    ARGS = parser.parse_args()

    #### Check the environment's spaces ################################################################
    env = gym.make("flythrugate-aviary-v0")
    print("[INFO] Action space:", env.action_space)
    print("[INFO] Observation space:", env.observation_space)
    check_env(env, warn=True, skip_render_check=True)

    #### Train the model ###############################################################################
    if not ARGS.rllib:
        model = A2C(MlpPolicy, env, verbose=1)
        model.learn(total_timesteps=500000)
    else:
        ray.shutdown(); ray.init(ignore_reinit_error=True)
        register_env("flythrugate-aviary-v0", lambda _: FlyThruGateAviary())
        config = ppo.DEFAULT_CONFIG.copy()
        config["num_workers"] = 2
        config["env"] = "flythrugate-aviary-v0"
        agent = ppo.PPOTrainer(config)
        for i in range(100):
            results = agent.train()
            print("[INFO] {:d}: episode_reward max {:f} min {:f} mean {:f}".format(i, \
                    results["episode_reward_max"], results["episode_reward_min"], results["episode_reward_mean"]))
        policy = agent.get_policy()
        print(policy.model.base_model.summary())
        ray.shutdown()

    #### Show (and record a video of) the model's performance ##########################################
    env = FlyThruGateAviary(gui=True, record=True)
    obs = env.reset()
    start = time.time()
    for i in range(10*env.SIM_FREQ):
        if not ARGS.rllib: action, _states = model.predict(obs, deterministic=True)
        else: action, _states, _dict = policy.compute_single_action(obs)
        obs, reward, done, info = env.step(action)
        env.render()
        sync(i, start, env.TIMESTEP)
        print()
        print(done)
        print()
        if done: obs = env.reset()
    env.close()