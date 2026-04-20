import random

from .purple import fill_blank as fill_blank_module
from .purple import homophone_generator as homophone_module
from .purple import sports_players as sports_players_module


class PurpleGenerator:
    """Generate harder (purple-level) Connections-style categories.

    This class randomly chooses one generator from the generators/purple package,
    calls it, prints the returned result, and returns it.
    """

    def __init__(self):
        self.generators = [
            fill_blank_module.generate,
            sports_players_module.generate,
        ]

    def generate(self):
        generator = random.choice(self.generators)
        result = generator()
        return result


def make():
    return PurpleGenerator()

if __name__ == '__main__':
    inst = make()
    res = inst.generate()
    print(res)