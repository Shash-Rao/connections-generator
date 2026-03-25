import random
from nltk.corpus import wordnet as wn
from utils.filters import is_good_category, get_valid_words_from_synset


class SemanticGenerator:
    def __init__(self):
        self.synsets = list(wn.all_synsets('n'))

    def generate(self):
        random.shuffle(self.synsets)

        for syn in self.synsets:
            if not is_good_category(syn):
                continue

            hyponyms = syn.hyponyms()
            if len(hyponyms) < 6:
                continue

            candidates = []

            for h in hyponyms:
                candidates.extend(get_valid_words_from_synset(h))

            candidates = list(set(candidates))

            if len(candidates) < 4:
                continue

            words = random.sample(candidates, 4)

            return {
                "category": syn.lemmas()[0].name().replace("_", " "),
                "words": words,
                "meta": {
                    "synset": syn
                }
            }

        return None