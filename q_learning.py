import sys

import random
from statistics import mean

import gym
from aalpy.learning_algs import run_Alergia, run_JAlergia

import gym_partially_observable_grid
import numpy as np

debug = False
from termcolor import colored
import copy

# Make environment deterministic even if it is stochastic
from tempest_shields import TempestInterface
from utils import writeSamplesToFile, deleteSampleFile

world_file=sys.argv[1]
setting=sys.argv[2]
threshold=sys.argv[3]

force_determinism = False
# Add slip to the observation set (action failed). Only necessary if is_partially_obs is set to True AND you want
# the underlying system to behave like deterministic MDP.
indicate_slip = False
# Use abstraction/partial observability. If set to False, (x,y) coordinates will be used as outputs
is_partially_obs = False
indicate_wall = False
# If one_time_rewards is set to True, reward in single location will be obtained only once per episode.
# Otherwise, reward will be given every time
one_time_rewards = True
step_penalty = 0.5

env = gym.make(id='poge-v1',
               world_file_path=world_file,
               force_determinism=force_determinism,
               indicate_slip=indicate_slip,
               is_partially_obs=is_partially_obs,
               indicate_wall=indicate_wall,
               one_time_rewards=one_time_rewards,
               step_penalty=step_penalty)

# Hyper parameters
alpha = 0.1
gamma = 0.9

num_training_episodes = 30000
interval_size = 1000

forbidden_state_reward = -100

# For plotting metrics
all_epochs = []


def safe_argmax(q_table, state, shield):
    safe_action_selected = False
    action_value_indices = list(q_table[state].argsort())
    action = None
    while not safe_action_selected and action_value_indices is not None:
        action = action_value_indices.pop()
        if shield.is_safe(env.action_space_to_act_map[action]):
            safe_action_selected = True

    if not safe_action_selected:
        action = np.argmax(q_table[state])
    return action


#def get_abstract_output(state, reward):
#    x, y = env.decode(state)
#    if env.abstract_world[x][y] == 'd':
#        output = 'death'
#    elif reward == env.goal_reward:
#        output = 'GOAL'
#    else:
#        output = f's{x}_{y}'
#    return output

def get_abstract_output(state, reward):
    x, y = env.decode(state)
    if env.abstract_world[x][y] == 'd':
        output = 'death'
    elif reward == env.goal_reward:
        output = 'GOAL'
    else:
        output = env.abstract_world[x][y]
        if x + 1 < len(env.abstract_world) and env.abstract_world[x+1][y] == 'd':
            output += 'death_r'
        if x-1 >= 0 and env.abstract_world[x-1][y] == 'd':
            output += 'death_l'
        if y+1 < len(env.abstract_world[x]) and env.abstract_world[x][y+1] == 'd':
            output += 'death_u'
        if y-1 >= 0 and env.abstract_world[x][y-1] == 'd':
            output += 'death_d'
    return output


def train_agent(training_type='no_penalty', verbose=False):
    epsilon = 0.4
    epsilon_threshold = 0.1
    assert training_type in {'no_penalty', 'penalty', 'shielded'}

    deleteSampleFile();
    ep_reward = []
    training_forbidden = 0

    print(f'Training for {training_type} started.')

    training_data = []
    model = None
    tempest_interface = None

    q_table = np.zeros([env.observation_space.n, env.action_space.n])

    for i in range(1, num_training_episodes + 1):
        #print(f"Episode {i}")
        epsilon = epsilon*0.9999
        if epsilon < epsilon_threshold: epsilon = epsilon_threshold
        if i % interval_size == 0:

            poscount=0
            if debug:
                for r in ep_reward:
                    if r <= 0:
                        print(colored(r, "red"), end=",")
                    elif r <= 40:
                        print(colored(r, "blue"), end=",")
                    else:
                        print(colored(r, "green"), end=",")
                        poscount=poscount+1
            if debug: print(f"\nPoscount: {poscount} / {interval_size}")
            print("")
            if verbose:
                print(f'Episodes [{i - interval_size}, {i}]')
                print(f'Avg. reward:                {mean(ep_reward)}')
                print(f'Avg. forbidden frequency:   {training_forbidden // interval_size}')
                print('--------------------------------------------------------')
            ep_reward.clear()
            training_forbidden = 0
            if debug: input("")

            if training_type == 'shielded':
                writeSamplesToFile(training_data)
                model = run_JAlergia(path_to_data_file='alergiaSamples.txt', automaton_type='mdp', eps=0.005,
                                     path_to_jAlergia_jar='alergia.jar', heap_memory='-Xmx12g')
                #training_data.clear()

                tempest_interface = TempestInterface("GOAL", model, 2, "death", threshold)

        state = env.reset()
        if training_type == 'shielded' and tempest_interface is not None:
            tempest_interface.reset()

        episode_steps = [get_abstract_output(state, 0)]

        culmalative_reward = 0
        done = False
        while not done:
            if random.random() < epsilon:
                if training_type == 'shielded' and tempest_interface is not None:
                    action = env.actions_dict[random.sample(tempest_interface.get_safe_action_space(),1)[0]]
                else:
                    action = env.action_space.sample()
            else:
                if training_type != 'shielded' or tempest_interface is None:
                    action = np.argmax(q_table[state])
                else:
                    action = safe_argmax(q_table, state, tempest_interface)
            #if training_type == 'shielded' and tempest_interface is not None: print(f"playerlocation: {env.player_location[0]}, {env.player_location[1]} action: {env.action_space_to_act_map[action]}, shield state: {tempest_interface.current_state}")

            next_state, reward, done, info = env.step(action)
            x, y = env.player_location[0], env.player_location[1]

            # add for Alergia
            if training_type == 'shielded':
                output = get_abstract_output(next_state, reward)
                action_name = env.action_space_to_act_map[action]
                if tempest_interface is not None:
                    tempest_interface.step_to(action_name, output)
                episode_steps.append((action_name, output))

            # If forbidden state is reached
            if env.abstract_world[x][y] == 'd':
                training_forbidden += 1
                if training_type == 'penalty' or training_type == 'shielded':
                    reward = forbidden_state_reward
                done = True

                #print(f"Episode: {episode_steps}, location: {env.player_location}")
                #input("")

            old_value = q_table[state, action]

            next_max = np.max(q_table[next_state])

            new_value = (1 - alpha) * old_value + alpha * (reward + gamma * next_max)
            q_table[state, action] = new_value

            culmalative_reward += reward
            if done:
                ep_reward.append(culmalative_reward)
                training_data.append(episode_steps)

            state = next_state

    print("Training finished.")
    deleteSampleFile()
    return q_table, tempest_interface


def train_all_agents():
    return train_agent('no_penalty'), train_agent('penalty'), train_agent('shielded')


def evaluate_agent(agent_q_table, shield=None, num_ep=100):
    episodes = num_ep

    goals_reached = 0
    forbidden_state_reached = 0
    total_steps = 0


    for _ in range(episodes):
        state = env.reset()
        if shield:
            shield.reset()

        done = False

        while not done:
            action = np.argmax(agent_q_table[state]) if shield is None else safe_argmax(q_table, state, shield)
            #if debug: print(f"[({env.player_location[0], env.player_location[1]}) [{state}]", end=": ")
            #if debug and shield:  print(f"allowed actions: {shield.get_safe_actions(state)}", end="")
            state, reward, done, info = env.step(action)
            #if debug: print(f"reward: {reward}]  ->", end="")

            if shield:
                output = get_abstract_output(state, reward)
                #print(f" \n output: {output}", end="")
                shield.step_to(env.action_space_to_act_map[action], output)

            x, y = env.player_location[0], env.player_location[1]
            if env.abstract_world[x][y] == 'd':
                reward = forbidden_state_reward
                forbidden_state_reached += 1
                done = True

            if reward == env.goal_reward and done:
                goals_reached += 1

            total_steps += 1

        #if debug: input("")

    print(f"Results after {episodes} episodes:")
    print(f"Total Number of Goal reached: {goals_reached}")
    print(f"Average timesteps per episode: {total_steps / episodes}")


q_table, shield = train_agent(setting, verbose=True)
#shield.print_shield()
#input("")
evaluate_agent(q_table, shield, 1000)
