import random
from collections import Counter
from statistics import mean
from time import sleep

import gym
import gym_partially_observable_grid

from aalpy.base import SUL
from aalpy.learning_algs import run_active_Alergia
from aalpy.learning_algs.stochastic_passive.ActiveAleriga import Sampler
from aalpy.utils import visualize_automaton, save_automaton_to_file, load_automaton_from_file

from tempest_shields import TempestInterface
from utils import StochasticWorldSUL, test_model_with_tempest


class SafeSampler(Sampler):
    def __init__(self, input_al, eps=0.9, num_new_samples=2000, min_seq_len=10, max_seq_len=50):
        self.eps = eps
        self.new_samples = num_new_samples
        self.input_al = input_al
        self.min_seq_len = min_seq_len
        self.max_seq_len = max_seq_len

    def sample(self, sul, model):
        # Here you get a current model
        # visualize_automaton(model)

        # TODO extract unsafe states from the model
        unsafe_state_ids = set()
        for s in model.states:
            if s.output in {'death', 'unsafe1', 'unsafe2'}:
                unsafe_state_ids.add(s.output)

        new_data = []

        # I guess you can keep the overall structure the same (reset, step,...)
        tempest_interface = TempestInterface("GOAL", model, None, "death")
        completely_random = True if tempest_interface.property_val < 0.5 else False

        for _ in range(self.new_samples):
            sample = ['Init']
            sul.pre()
            tempest_interface.reset()
            continue_random = completely_random

            for _ in range(random.randint(self.min_seq_len, self.max_seq_len)):
                if not continue_random and random.random() < self.eps:
                    # TODO get a step from tempest
                    i = tempest_interface.get_input()
                    if i is None:
                        i = random.choice(self.input_al)
                else:
                    i = random.choice(self.input_al)

                o = sul.step(i)
                sample.append((i, o))

                # if observed output is not reachable in the model
                continue_random = not tempest_interface.step_to(i, o)

            sul.post()
            new_data.append(sample)

        return new_data


def get_initial_data(sul, input_al, initial_sample_num=5000, min_seq_len=10, max_seq_len=50):
    # Generate random initial samples
    random_samples = []
    for _ in range(initial_sample_num):
        sample = ['Init']
        sul.pre()
        for _ in range(random.randint(min_seq_len, max_seq_len)):
            i = random.choice(input_al)
            o = sul.step(i)
            sample.append((i, o))
        sul.post()
        random_samples.append(sample)
    return random_samples


# Make environment deterministic even if it is stochastic
force_determinism = False
# Add slip to the observation set (action failed)
indicate_slip = True
# Use abstraction/partial observability. If set to False, (x,y) coordinates will be used as outputs
is_partially_obs = True

min_seq_len, max_seq_len = 10, 50

world = gym.make(id='poge-v1',
                 world_file_path='worlds/unsafe_world1.txt',
                 force_determinism=force_determinism,
                 indicate_slip=indicate_slip,
                 is_partially_obs=is_partially_obs,
                 one_time_rewards=True)

input_al = list(world.actions_dict.keys())

sul = StochasticWorldSUL(world)

data = get_initial_data(sul, input_al, initial_sample_num=10000, min_seq_len=min_seq_len, max_seq_len=max_seq_len)

sampler = SafeSampler(input_al, eps=0.9, num_new_samples=2000, min_seq_len=min_seq_len, max_seq_len=max_seq_len)

final_model = run_active_Alergia(data=data, sul=sul, sampler=sampler, n_iter=5)
# final_model = load_automaton_from_file('passive_active.dot', automaton_type='mdp')
print(f'Final model size: {final_model.size}')
# save_automaton_to_file(final_model, 'passive_active')

test_model_with_tempest(final_model, sul, input_al, num_episodes=100)
