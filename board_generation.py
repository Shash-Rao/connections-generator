import json
import random
import os
from collections import defaultdict


# --- Load all JSON files from /categories ---
def load_categories_from_folder(folder_path):
    all_categories = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, "r") as f:
                data = json.load(f)

                if not isinstance(data, list):
                    raise ValueError(f"{filename} does not contain a list")

                all_categories.extend(data)

    return all_categories


# --- Group by difficulty ---
def group_by_difficulty(categories):
    categories_by_difficulty = defaultdict(list)
    for cat in categories:
        categories_by_difficulty[cat["difficulty"]].append(cat)
    return categories_by_difficulty


# --- Validation ---
def is_valid_board(selected_categories):
    seen_words = set()
    seen_category_wordsets = set()

    for cat in selected_categories:
        words = cat["words"]

        # prevent identical category word sets
        wordset_key = tuple(sorted(words))
        if wordset_key in seen_category_wordsets:
            return False
        seen_category_wordsets.add(wordset_key)

        # prevent word overlap
        for word in words:
            if word in seen_words:
                return False
            seen_words.add(word)

    return True


# --- Generate a single board ---
def generate_board(categories_by_difficulty, required_difficulties, max_attempts=1000):
    for _ in range(max_attempts):
        selected = [
            random.choice(categories_by_difficulty[d])
            for d in required_difficulties
        ]

        if is_valid_board(selected):
            return selected

    raise RuntimeError("Failed to generate a valid board after many attempts")


# --- Generate UNIQUE boards ---
def generate_unique_boards(n_boards, categories_by_difficulty, required_difficulties):
    boards = []
    seen_board_keys = set()

    attempts = 0

    while len(boards) < n_boards:
        board = generate_board(categories_by_difficulty, required_difficulties)
        attempts += 1

        # Create board signature (16 words, order-independent)
        board_words = [word for cat in board for word in cat["words"]]
        board_key = tuple(sorted(board_words))

        if board_key not in seen_board_keys:
            seen_board_keys.add(board_key)
            boards.append(board)

            if len(boards) % 1000 == 0:
                print(f"Generated {len(boards)} unique boards (attempts: {attempts})")

        # Optional: safety check to avoid infinite loops
        if attempts > n_boards * 20:
            raise RuntimeError("Too many attempts — dataset may not support enough unique boards")

    return boards


# --- Printing utilities ---
def print_board_grid(board):
    words = []
    for cat in board:
        words.extend(cat["words"])

    random.shuffle(words)

    print("\nGrid:")
    for i in range(0, 12, 4):
        print(" | ".join(words[i:i+4]))


def print_solution(board):
    print("\nSolution:")
    for cat in board:
        difficulty = cat["difficulty"].upper()
        name = cat["category_name"]
        words = ", ".join(cat["words"])
        print(f"[{difficulty}] {name}: {words}")


def preview_boards(boards, n=10):
    sample = random.sample(boards, min(n, len(boards)))

    for i, board in enumerate(sample, 1):
        print("\n==============================")
        print(f"Board {i}")
        print("==============================")

        print_board_grid(board)
        print_solution(board)


# --- Main ---
def main():
    folder = "categories"
    required_difficulties = ["yellow", "green", "blue"]#, "purple"]

    categories = load_categories_from_folder(folder)
    categories_by_difficulty = group_by_difficulty(categories)

    # Validate difficulties exist
    for d in required_difficulties:
        if d not in categories_by_difficulty or not categories_by_difficulty[d]:
            raise ValueError(f"No categories found for difficulty: {d}")

    # Generate 10k UNIQUE boards
    boards = generate_unique_boards(
        n_boards=10_000,
        categories_by_difficulty=categories_by_difficulty,
        required_difficulties=required_difficulties,
    )

    # Save
    with open("boards.json", "w") as f:
        json.dump(boards, f, indent=2)

    print("\nFinished generating unique boards.")

    # Preview
    preview_boards(boards, n=10)


if __name__ == "__main__":
    main()