import json
import random
import os
from collections import defaultdict


class BoardGenerator:
    def __init__(self, folder_path, required_difficulties=None):
        self.folder_path = folder_path
        self.required_difficulties = required_difficulties or ["yellow", "green", "blue", "purple"]

        self.categories = self._load_categories()
        self.categories_by_difficulty = self._group_by_difficulty()

        self._validate_difficulties()

        # global uniqueness tracking
        self.seen_board_keys = set()

    # --- Loading ---
    def _load_categories(self):
        all_categories = []

        for filename in os.listdir(self.folder_path):
            if filename.endswith(".json"):
                filepath = os.path.join(self.folder_path, filename)
                with open(filepath, "r") as f:
                    data = json.load(f)

                    if not isinstance(data, list):
                        raise ValueError(f"{filename} does not contain a list")

                    all_categories.extend(data)

        return all_categories

    def _group_by_difficulty(self):
        categories_by_difficulty = defaultdict(list)
        for cat in self.categories:
            categories_by_difficulty[cat["difficulty"]].append(cat)
        return categories_by_difficulty

    def _validate_difficulties(self):
        for d in self.required_difficulties:
            if d not in self.categories_by_difficulty or not self.categories_by_difficulty[d]:
                raise ValueError(f"No categories found for difficulty: {d}")

    # --- Validation ---
    def _is_valid_board(self, selected_categories):
        seen_words = set()
        seen_category_wordsets = set()

        for cat in selected_categories:
            words = cat["words"]

            wordset_key = tuple(sorted(words))
            if wordset_key in seen_category_wordsets:
                return False
            seen_category_wordsets.add(wordset_key)

            for word in words:
                if word in seen_words:
                    return False
                seen_words.add(word)

        return True

    # --- Generation ---
    def _generate_board(self, max_attempts=1000):
        for _ in range(max_attempts):
            selected = [
                random.choice(self.categories_by_difficulty[d])
                for d in self.required_difficulties
            ]

            if self._is_valid_board(selected):
                return selected

        raise RuntimeError("Failed to generate a valid board after many attempts")

    def _board_key(self, board):
        words = [word for cat in board for word in cat["words"]]
        return tuple(sorted(words))

    def generate_unique_boards(self, n_boards):
        boards = []
        attempts = 0

        while len(boards) < n_boards:
            board = self._generate_board()
            attempts += 1

            key = self._board_key(board)

            if key not in self.seen_board_keys:
                self.seen_board_keys.add(key)
                boards.append(board)

                if len(boards) % 1000 == 0:
                    print(f"Generated {len(boards)} unique boards (attempts: {attempts})")

            if attempts > n_boards * 20:
                raise RuntimeError("Too many attempts — dataset may be exhausted")

        print(f"\nFinal: {len(boards)} boards generated in {attempts} attempts")
        return boards

    # --- Output ---
    def save_boards(self, boards, filepath="output/boards.json"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(boards, f, indent=2)

    # --- Preview ---
    def print_board_grid(self, board):
        words = [word for cat in board for word in cat["words"]]
        random.shuffle(words)

        print("\nGrid:")
        for i in range(0, 16, 4):
            print(" | ".join(words[i:i+4]))

    def print_solution(self, board):
        print("\nSolution:")
        for cat in board:
            difficulty = cat["difficulty"].upper()
            name = cat["category_name"]
            words = ", ".join(cat["words"])
            print(f"[{difficulty}] {name}: {words}")

    def preview_boards(self, boards, n=10):
        sample = random.sample(boards, min(n, len(boards)))

        for i, board in enumerate(sample, 1):
            print("\n==============================")
            print(f"Board {i}")
            print("==============================")

            self.print_board_grid(board)
            self.print_solution(board)


# --- Usage ---
if __name__ == "__main__":
    generator = BoardGenerator(folder_path="categories")

    boards = generator.generate_unique_boards(10_000)
    generator.save_boards(boards)
    generator.preview_boards(boards, n=10)