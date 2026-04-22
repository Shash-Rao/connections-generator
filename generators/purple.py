import json
import random
import os

from .purple_generators import fill_blank as fill_blank_module
from .purple_generators import homophone_generator as homophone_module
from .purple_generators import sports_players as sports_players_module

from .base import BaseGenerator


class PurpleGenerator(BaseGenerator):
    """Generate harder (purple-level) Connections-style categories.

    This class randomly chooses one generator from the generators/purple package,
    calls it, prints the returned result, and returns it.
    """

    def __init__(self):
        self.generators = [
            fill_blank_module.generate,
            sports_players_module.generate,
        ]
        self.generator_names = {
            fill_blank_module.generate: "fill_blank.json",
            sports_players_module.generate: "sports_players.json"
        }

    def generate_group(self, generator=None):
        if not generator:
            generator = random.choice(self.generators)
        result = generator()
        return result
    
    def generate_json(self, output_dir="categories", n=500):
        os.makedirs(output_dir, exist_ok=True)

        for generator in self.generators:
            results = []
            for _ in range(n):
                result = self.generate_group(generator)
                results.append(result)
            filename = output_dir + "/" + self.generator_names[generator]
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nSaved {n} categories to {filename}\n")


def make():
    return PurpleGenerator()

if __name__ == '__main__':
    inst = make()
    inst.generate_json()