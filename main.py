from generators.semantic import SemanticGenerator
from generators.anagram import AnagramGenerator
from generators.synonym import SynonymGenerator
from generators.purple import PurpleGenerator

from board.board_generation import BoardGenerator

from utils.seeds import SEED_SUBJECTS

if __name__ == "__main__":

    generators = [
        SynonymGenerator(), 
        SemanticGenerator(SEED_SUBJECTS), 
        AnagramGenerator(), 
        PurpleGenerator()
    ]

    for gen in generators:
        gen.generate_json()

    bg = BoardGenerator(folder_path="categories")

    boards = bg.generate_unique_boards(10_000)
    bg.save_boards(boards)
    bg.preview_boards(boards, n=10)