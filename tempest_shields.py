from pathlib import Path

import os

from aalpy.utils import mdp_2_prism_format

#tempest_binary = "/home/msi/tempest-shields/build/bin/storm"
tempest_binary = "/home/stefan/projects/tempest-public/build/bin/storm"

debug = False

input_cardinality = 4
inputs = ["left", "right", "up", "down"]


class TempestInterface:
    def __init__(self, dest, model, num_steps=None, safety=None, threshold=None):
        self.tmp_dir = Path("tmp")
        self.dest = dest
        self.safety = safety
        self.model = model
        self.model_dict = None
        self.num_steps = num_steps
        self.tmp_mdp_file = (self.tmp_dir / f"po_rl_{dest}.prism")
        self.tmp_properties_file = (self.tmp_dir / f"po_rl_{dest}.prop")
        # self.tmp_prop_file = f"{self.tmp_dir_name}/po_rl.props"
        self.current_state = None
        self.tmp_dir.mkdir(exist_ok=True)
        self.introduce_self_loops()
        mdp_2_prism_format(self.model, "porl", output_path=self.tmp_mdp_file)
        self.property_val = 0
        self.threshold = threshold
        self.safety_shield = None # = TempestShieldParser(f"safety_shield_{self.safety}.shield")
        self.reachability_probabilities = None #TempestShieldParser(f"eventually_shield_{self.dest}.shield")
        self.call_tempest()

    def introduce_self_loops(self):
        for state in self.model.states:
            if len(state.transitions) != input_cardinality:
                for inp in inputs:
                    if not inp in state.transitions:
                        state.transitions[inp] = [(state, 1.0)]


    def create_safety_shielding_property(self):
        assert self.threshold is not None
        if not self.num_steps:
            prop = f"<safety_shield_{self.safety}, PreSafety, lambda={self.threshold}> <<robot>> Pmax=?[G !\"{self.safety}\"];"
        else:
            prop = f'<safety_shield_{self.safety}, PreSafety, lambda={self.threshold}> <<robot>> Pmax=?[G<{self.num_steps} !\"{self.safety}\"];'
        return prop
        return None

    def create_eventually_shielding_property(self):
        if not self.num_steps:
            prop = f"<eventually_shield_{self.dest}, PreSafety, gamma=0.0> <<robot>> Pmax=?[F \"{self.dest}\"];"
        else:
            prop = f'<safety_shield_{self.dest}, PreSafety, gamma=0.0> <<robot>> Pmax=?[F<{self.num_steps} \"{self.dest}\"];'
        return prop

    def create_property_file(self):
        with open(self.tmp_properties_file, "w") as properties_file:
            if self.safety:
                properties_file.write(self.create_safety_shielding_property())
                properties_file.write("\n")
            #properties_file.write(self.create_eventually_shielding_property())

    def get_input(self):
        if self.current_state is None:
            return None
        else:
            available_actions = sorted(self.reachability_probabilities.transitions_dict[self.current_state],
                                       key=lambda a: a.probability, reverse=True)

            safe_actions = []
            if self.safety:
                safe_actions = [pair.action for pair in self.safety_shield.transitions_dict[self.current_state]]

            i = 0
            if self.safety:
                while available_actions[i].action not in safe_actions:
                    i += 1
            return available_actions[i].action

    def print_shield(self):
        assert self.safety_shield is not None
        for k in self.safety_shield.transitions_dict:
            print(f"State {k}:")
            for action in self.safety_shield.transitions_dict[k]:
                print(f"{action.action} : {action.probability}", end=", ")
            print("")



    def is_safe(self, action):
        #assert self.safety_shield is not None
        if not self.safety_shield:
            return True
        if not self.current_state:
            return True
        #for k in self.safety_shield.transitions_dict:
        #    print(f"{k}: {self.safety_shield.transitions_dict[k]}")
        #print(f"Testing safe actions for state (loc) {self.current_state} and action {action}")
        #print(f"safe actions are {self.get_safe_actions()}")
        try:
            safe_actions = [pair.action for pair in self.safety_shield.transitions_dict[self.current_state]]
            return action in safe_actions
        except:
            for k in self.model.states:
                print(f"{k.output}")
            for k in sorted(self.safety_shield.transitions_dict):
                print(f"{k}: {self.safety_shield.transitions_dict[k]}")
            print(f"{len(self.model.states)}")

            #for k in self.model.states
            assert False

    def get_safe_action_space(self):
        safe_action_space = []
        for action in self.safety_shield.transitions_dict[self.current_state]:
            safe_action_space.append(action.action)
        return safe_action_space

    def get_safe_actions(self):
        human_string = ""
        for action in self.safety_shield.transitions_dict[self.current_state]:
            human_string += f"{action.action}<{action.probability}>, "
        return human_string

    def reset(self):
        self.current_state = 'q0'

    def step_to(self, input, output):
        found_state = False
        #print()
        for state in self.model.states:
            if state.state_id != self.current_state:
                continue
            for ns in state.transitions[input]:

                if ns[0].output == output:
                    found_state = True
                    self.current_state = ns[0].state_id
                    return found_state

        return found_state

    def call_tempest(self):
        import subprocess
        from os import path

        self.property_val = 0

        safety_in_model = False
        for s in self.model.states:
            if s.output == self.safety:
                safety_in_model = True
                break

        if not safety_in_model:
            print('\t\t[WARN] SHIELD NOT COMPUTED')
            return self.property_val

        model_abs_path = path.abspath(self.tmp_mdp_file)
        mdp_file = open(model_abs_path, "rt")

        game_header = """
smg
player robot
  [up], [down], [left], [right]
endplayer
player none
  none
endplayer
module none
endmodule """
        data = mdp_file.read()
        data = data.replace('mdp', game_header)
        mdp_file.close()
        mdp_file = open(model_abs_path, "wt")
        mdp_file.write(data)
        mdp_file.close()

        os.system("rm -rf safety_shield_death.shield")
        self.create_property_file()
        proc = subprocess.Popen(
            [tempest_binary, "--prism", model_abs_path, "--prop", self.tmp_properties_file, "--buildstateval", "--buildchoicelab"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = proc.communicate()[0]
        out = out.decode('utf-8').splitlines()
        for line in out:
            #print(line)
            if not line:
                continue
            if 'Syntax error' in line:
                print(line)
            else:
                if "Result" in line:
                    result_content = line.split(' ')
                    try:
                        self.property_val = float(result_content[-1])
                    except ValueError:
                        print("Result parsing error")
        print(f"Probability to satisfy: {self.property_val}")
        if debug: input("cat tmp file")
        proc.kill()
        self.safety_shield = TempestShieldParser(f"safety_shield_{self.safety}.shield")
        #self.reachability_probabilities TempestShieldParser(f"eventually_shield_{self.dest}.shield")
        return self.property_val


class ActionProbTuple:
    def __init__(self, probability, action):
        self.probability = probability
        self.action = action


class TempestShieldParser:
    def __init__(self, shield_file):
        num_shield_header_lines = 3
        self.transitions_dict = dict()
        with open(shield_file, "r") as f:
            self.shield_file_content = f.readlines()
        for line in self.shield_file_content[num_shield_header_lines:-1]:
            state = str('q' + line[line.find("[") + 1:line.find("]")].split("=")[-1])
            safe_actions = list()
            for action in line[line.find("]") + 1:-1].split(";"):
                probability = float(action[0:action.find(":")])
                action_label = action[action.find("{") + 1:action.find("}")]
                safe_actions.append(ActionProbTuple(probability, action_label))
            self.transitions_dict[state] = safe_actions
