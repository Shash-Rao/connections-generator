from generators.semantic import SemanticGenerator
from scoring.embedding_scorer import score
from generators.synonym_generator import SynonymGenerator
from scoring.difficulty import assign_difficulties
import numpy as np


def generate_best(generator, attempts=200):
    best = None
    best_score = float("-inf")

    for _ in range(attempts):
        group = generator.generate()
        if not group:
            continue

        s = score(group)

        if s > best_score:
            best_score = s
            best = group

    return best, best_score


if __name__ == "__main__":
    gen = SynonymGenerator()
    # group, s = generate_best(gen, attempts=300)

    # print("\nBest Group:")
    # print(group["category"])
    # print(", ".join(group["words"]))
    # print(f"\nScore: {s:.3f}")

    attempts = 50

    groups = []
    for _ in range(attempts):
        group = gen.generate()
        if not group:
            continue

        s = score(group)

        if s != float("-inf"):
            groups.append(group)
            #groups.append({"category": group["category"], "words": group["words"], "score": s})

    # scores = [g["score"] for g in groups if g["score"] != float("-inf")]
    # print(scores)
    # threshold = np.percentile(scores, 80)

    # print(f"Threshold: {threshold}")

    # for g in groups:
    #     if g["score"] > threshold:
    #         print("\nGroup:")
    #         print(g["category"])
    #         print(", ".join(g["words"]))
    #         print(f"\nScore: {g["score"]:.3f}")

    groups = assign_difficulties(groups)

    for g in groups:
        print(f"\nGroup: {g['category']}")
        print(f"Difficulty: {g['difficulty']}")
        print(", ".join(g["words"]))
        #print(f"\nScore: {g["score"]:.3f}")