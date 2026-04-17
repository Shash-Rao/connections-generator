from generators.anagram import AnagramGenerator
from scoring.embedding_scorer import score
from generators.synonym_generator import SynonymGenerator
from scoring.difficulty import assign_difficulties


if __name__ == "__main__":
    gen = AnagramGenerator(n_words=200000, min_zipf=3.0, debug=True)

    # Inspect the pool directly
    gen.debug_print_buckets(limit=25)
    gen.debug_print_bucket_scores(limit=25)

    # Build one canonical group per anagram family
    groups = gen.generate_all_canonical_groups()

    print(f"\nCanonical anagram groups before scoring: {len(groups)}")

    # Score and keep only valid groups
    kept = []
    seen_keys = set()

    for group in groups:
        fam_key = group["meta"]["key"]

        if fam_key in seen_keys:
            continue

        seen_keys.add(fam_key)

        s = score(group)
        if s != float("-inf"):
            group["score"] = s
            kept.append(group)

    print(f"Canonical anagram groups after scoring: {len(kept)}")

    if not kept:
        print("\nNo valid groups survived scoring.")
    else:
        kept = assign_difficulties(kept)

        # Print best-scoring groups first
        kept.sort(key=lambda g: g["score"], reverse=True)

        print("\nFinal groups:")
        for g in kept[:20]:
            print(f"\nGroup: {g['category']}")
            print(f"Difficulty: {g['difficulty']}")
            print(f"Score: {g['score']:.3f}")
            print(", ".join(g["words"]))
