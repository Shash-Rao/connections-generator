from collections import defaultdict
import random

from wordfreq import zipf_frequency

from utils.anagram_utils import (
    load_words,
    is_valid_word,
    sort_letters,
    passes_frequency,
    too_trivial,
)


class AnagramGenerator:
    def __init__(self, n_words=200000, min_zipf=3.0, debug=True):
        self.n_words = n_words
        self.min_zipf = min_zipf
        self.debug = debug

        self.words = load_words(n=n_words, debug=debug)
        self.buckets = self._build_index(self.words)
        self.filtered_buckets = self._build_filtered_buckets(min_zipf=min_zipf)
        self.valid_keys = list(self.filtered_buckets.keys())

        if self.debug:
            print(f"Total valid keys: {len(self.valid_keys)}")

    def _build_index(self, words):
        buckets = defaultdict(list)

        for w in words:
            if not is_valid_word(w):
                continue

            key = sort_letters(w)
            buckets[key].append(w)

        return buckets

    def _build_filtered_buckets(self, min_zipf=3.0):
        filtered = {}

        total_buckets = len(self.buckets)
        buckets_ge4_raw = 0
        buckets_ge4_common = 0

        for key, words in self.buckets.items():
            unique_words = sorted(set(words))

            if len(unique_words) < 4:
                continue
            buckets_ge4_raw += 1

            good_words = [
                w for w in unique_words
                if passes_frequency([w], min_zipf=min_zipf)
            ]

            if len(good_words) < 4:
                continue
            buckets_ge4_common += 1

            if too_trivial(good_words):
                continue

            filtered[key] = good_words

        if self.debug:
            print(f"Total buckets: {total_buckets}")
            print(f"Buckets with >=4 raw words: {buckets_ge4_raw}")
            print(f"Buckets with >=4 common words: {buckets_ge4_common}")
            print(f"Buckets after filtering: {len(filtered)}")

        return filtered

    def canonical_group_from_key(self, key):
        """
        Build one stable representative group for a given anagram family.
        This is useful for offline pool building.
        """
        if key not in self.filtered_buckets:
            return None

        candidates = self.filtered_buckets[key]

        if len(candidates) < 4:
            return None

        # Prefer more common words first, then alphabetical for stability
        candidates = sorted(
            candidates,
            key=lambda w: (-zipf_frequency(w, "en"), w)
        )

        words = candidates[:4]

        return {
            "category": "Anagrams",
            "words": words,
            "meta": {
                "type": "anagram",
                "key": key,
            }
        }

    def generate(self):
        """
        Randomly sample one anagram family, then return its canonical group.
        This keeps one representative per family instead of random 4-word subsets.
        """
        if not self.valid_keys:
            return None

        key = random.choice(self.valid_keys)
        return self.canonical_group_from_key(key)

    def generate_all_canonical_groups(self):
        """
        Useful for building an offline pool.
        """
        groups = []

        for key in self.valid_keys:
            group = self.canonical_group_from_key(key)
            if group is not None:
                groups.append(group)

        return groups

    def debug_print_buckets(self, limit=20):
        ranked = sorted(
            self.filtered_buckets.items(),
            key=lambda kv: (-len(kv[1]), kv[0])
        )

        print("\nTop anagram buckets:")
        for key, words in ranked[:limit]:
            print(f"{key} ({len(words)} words): {words}")

    def debug_print_bucket_scores(self, limit=20):
        scored = []

        for key, words in self.filtered_buckets.items():
            if len(words) < 4:
                continue

            avg_len = sum(len(w) for w in words) / len(words)
            avg_freq = sum(zipf_frequency(w, "en") for w in words) / len(words)

            score_val = avg_len + 0.25 * avg_freq
            scored.append((score_val, key, words))

        scored.sort(reverse=True)

        print("\nBest-looking buckets:")
        for score_val, key, words in scored[:limit]:
            print(f"{key} | score={score_val:.2f} | {words}")