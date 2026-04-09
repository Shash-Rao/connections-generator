from utils.anagram_utils import load_words, is_valid_word, sort_letters, passes_frequency, too_trivial
from wordfreq import top_n_list
from collections import defaultdict
import random

class AnagramGenerator:
    def __init__(self):
        self.words = load_words()
        self.buckets = self._build_index(self.words)
        self.valid_keys = self._filter_keys()

    def _build_index(self, words):
        buckets = defaultdict(list)
        for w in words:
            if not is_valid_word(w):
                continue
            key = sort_letters(w)
            buckets[key].append(w)
        return buckets

    def _filter_keys(self):
        valid = []
        for key, words in self.buckets.items():
            if len(words) < 4:
                continue

            if not passes_frequency(words):
                continue

            if too_trivial(words):
                continue

            valid.append(key)

        return valid

    def generate(self):
        for _ in range(50):  # retry loop
            key = random.choice(self.valid_keys)
            candidates = self.buckets[key]

            words = random.sample(candidates, 4)

            if not self._is_good_group(words):
                continue

            return {
                "category": "Anagrams",
                "words": words,
                "meta": {
                    "type": "anagram",
                    "key": key
                }
            }

        return None

    def _is_good_group(self, words):
        if len(set(words)) < 4:
            return False

        if any(len(w) < 3 for w in words):
            return False

        return True