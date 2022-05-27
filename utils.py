import random
from statistics import mean

from aalpy.base import SUL

from tempest_shields import TempestInterface


class StochasticWorldSUL(SUL):
    def __init__(self, stochastic_world):
        super().__init__()
        self.world = stochastic_world
        self.goal_reached = False
        self.is_done = False

    def pre(self):
        self.goal_reached = False
        self.is_done = False
        self.world.reset()

    def post(self):
        pass

    def step(self, letter):
        if letter is None:
            output = self.world.get_abstraction()
            if output[0].isdigit().isdigit():
                output = f'state_{output}'
            return output

        output, reward, done, info = self.world.step(self.world.actions_dict[letter])

        if reward == self.world.goal_reward or self.goal_reached:
            self.goal_reached = True
            return "GOAL"

        if done or self.is_done:
            self.is_done = True
            return "MAX_STEPS_REACHED"

        output = self.world.decode(output)
        if isinstance(output, tuple):
            output = f'{output[0]}_{output[1]}'
        if reward != 0:
            reward = reward if reward > 0 else f'neg_{reward * -1}'

        if output[0].isdigit():
            output = f'state_{output}'
        if reward != 0:
            output = f'{output}_r_{reward}'

        return output


def test_model_with_tempest(model, sul, input_al, num_episodes, max_ep_len=100):
    num_steps_per_ep = []
    goal_reached = 0
    max_steps_reached = 0
    unsafe_reached = 0

    tempest_interface = TempestInterface("GOAL", model)
    print(f'Goal Reachability: {tempest_interface.property_val}')

    for _ in range(num_episodes):
        step_counter = 0
        scheduler_step_valid = True
        sul.pre()
        tempest_interface.reset()
        while True:
            if step_counter == max_ep_len:
                break
            i = tempest_interface.get_input()
            if not scheduler_step_valid or i is None:
                i = random.choice(input_al)
            o = sul.step(i)
            # print(f"{step_counter: <4} Input: {i} leads to {o}")
            step_counter += 1
            scheduler_step_valid = tempest_interface.step_to(i, o)
            if o == 'GOAL':
                goal_reached += 1
                break
            if o == 'MAX_STEPS_REACHED':
                max_steps_reached += 1
                break
            if o == 'death':
                unsafe_reached += 1

        num_steps_per_ep.append(step_counter)
        sul.post()

    print(f'Tested on {num_episodes} episodes:')
    print(f'Goal reached  : {goal_reached}')
    print(f'Max Steps reached  : {max_steps_reached}')
    print(f'Unsafe reached  : {unsafe_reached}')
    print(f'Avg. step count : {mean(num_steps_per_ep)}')


def writeSamplesToFile(samples, path="alergiaSamples.txt"):
    with open(path, 'a') as f:
        for sample in samples:
            s = f'{str(sample.pop(0))}'
            for i, o in sample:
                s += f',{i},{o}'
            f.write(s + '\n')

    f.close()
    samples.clear()


def deleteSampleFile(path="alergiaSamples.txt"):
    import os
    if os.path.exists(path):
        os.remove(path)
