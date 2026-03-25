import random
from nltk.corpus import wordnet as wn
from wordfreq import zipf_frequency


# -----------------------
# CONFIG
# -----------------------

MIN_WORD_FREQ = 3.5   # higher = more common words
MIN_HYPONYMS = 8      # require enough children
SAMPLE_ATTEMPTS = 500


BAD_CATEGORIES = {
    "entity", "object", "thing", "whole", "artifact"
}


# -----------------------
# FILTERS
# -----------------------

def is_clean_word(word):
    return word.isalpha() and "_" not in word and "-" not in word


def is_common_word(word):
    return zipf_frequency(word, "en") >= MIN_WORD_FREQ


def is_good_category(syn):
    name = syn.lemmas()[0].name()

    if name in BAD_CATEGORIES:
        return False

    # Avoid overly general categories
    if syn.min_depth() < 5:
        return False

    return True


def get_valid_words_from_synset(syn):
    words = set()

    for lemma in syn.lemmas():
        w = lemma.name().lower()
        if is_clean_word(w) and is_common_word(w):
            words.add(w)

    return list(words)


# -----------------------
# GENERATOR
# -----------------------

class SemanticGenerator:
    def __init__(self):
        self.synsets = list(wn.all_synsets('n'))

    def generate_group(self):
        random.shuffle(self.synsets)

        for syn in self.synsets:
            if not is_good_category(syn):
                continue

            hyponyms = syn.hyponyms()

            if len(hyponyms) < MIN_HYPONYMS:
                continue

            candidates = []

            for h in hyponyms:
                words = get_valid_words_from_synset(h)
                candidates.extend(words)

            candidates = list(set(candidates))

            if len(candidates) < 4:
                continue

            # Sample group
            group = random.sample(candidates, 4)

            return {
                "category": syn.lemmas()[0].name().replace("_", " "),
                "words": group
            }

        return None


# -----------------------
# DRIVER
# -----------------------

def generate_multiple_groups(n=5):
    gen = SemanticGenerator()
    results = []

    for _ in range(n):
        group = None

        # Try multiple times per group
        for _ in range(50):
            group = gen.generate_group()
            if group:
                break

        if group:
            results.append(group)

    return results


# -----------------------
# MAIN
# -----------------------

if __name__ == "__main__":
    groups = generate_multiple_groups(10)

    for g in groups:
        print(f"\nCategory: {g['category']}")
        print(", ".join(g["words"]))