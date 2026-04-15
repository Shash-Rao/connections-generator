import random
from itertools import combinations
from nltk.corpus import wordnet as wn
from wordfreq import zipf_frequency


class SynonymGenerator:
    """
    Generates Connections-style synonym groups from WordNet.

    - Cursor-based iteration (no rescanning)
    - Global word dedup (no cross-group reuse, including morphological near-matches)
    - British/American spelling variant detection
    - Ambiguity-weighted scoring (prefers deceptive words)
    - Clean Connections-style category labels
    """

    def __init__(self):
        # Widened frequency band for more yield.
        # The embedding scorer will still reject truly obscure words
        # (it checks zipf >= 3.0), so this is safe to loosen here.
        self.min_zipf = 3.2
        self.max_zipf = 6.5

        self.pos_options = [wn.ADJ, wn.NOUN, wn.VERB]

        self.bad_words = {
            "thing", "object", "entity", "item", "stuff", "matter", "bit",
            "part", "portion", "unit", "act", "number", "one", "kind", "sort",
            "type", "member", "piece", "point", "place", "person", "people",
            "someone", "somebody", "anyone", "anything", "something",
            "way", "set", "lot", "group", "form", "case", "end", "line",
            "make", "get", "take", "give", "have", "come", "going",
            "good", "bad", "big", "new", "old", "great", "little",
            "much", "many", "well", "back", "just", "even", "also",
        }

        self.bad_gloss_words = {
            "entity", "object", "thing", "someone", "something", "anything",
            "anyone", "group", "kind", "sort", "type", "instance", "example",
            "part", "portion", "component", "quality", "property",
        }

        self.seen_groups = set()
        self.seen_words = set()

        self._ambiguity_cache = {}
        self._synsets = None
        self._cursor = 0

    # ------------------------------------------------------------------
    # Word cleaning & validation
    # ------------------------------------------------------------------

    def _clean_word(self, word):
        word = word.replace("_", " ").lower().strip()
        if " " in word or "-" in word:
            return None
        if len(word) < 3 or len(word) > 10:
            return None
        if not word.isalpha():
            return None
        if word in self.bad_words:
            return None
        return word

    def _is_good_frequency(self, word):
        z = zipf_frequency(word, "en")
        return self.min_zipf <= z <= self.max_zipf

    # ------------------------------------------------------------------
    # Morphological / spelling similarity detection
    # ------------------------------------------------------------------

    _SPELLING_NORMALIZATIONS = [
        ("our", "or"),
        ("ise", "ize"),
        ("isation", "ization"),
        ("yse", "yze"),
        ("ogue", "og"),
        ("ence", "ense"),
        ("ae", "e"),
        ("oe", "e"),
        ("grey", "gray"),
    ]

    def _normalize_spelling(self, word):
        result = word
        for brit, amer in self._SPELLING_NORMALIZATIONS:
            if brit in result:
                result = result.replace(brit, amer, 1)
        return result

    def _normalize_root(self, word):
        suffixes = [
            "ation", "ition", "ment", "ness", "ance", "ence", "able", "ible",
            "ting", "ring", "ning", "ing", "ful", "ous", "ive", "ial", "ual",
            "ity", "ery", "ory", "ary", "ier", "ies", "ied", "ers", "est",
            "eur", "our", "ant", "ent", "ion", "ism", "ist", "ure",
            "er", "ed", "ly", "al", "en", "es", "or", "ty",
            "s",
        ]
        root = word
        for suffix in suffixes:
            if len(root) > len(suffix) + 2 and root.endswith(suffix):
                if suffix == "ies":
                    root = root[:-3] + "y"
                else:
                    root = root[: -len(suffix)]
                break
        return root

    def _too_similar_pair(self, a, b):
        if a == b:
            return True
        if a in b or b in a:
            return True

        # British/American spelling variants
        if self._normalize_spelling(a) == self._normalize_spelling(b):
            return True

        # Root-based
        ra = self._normalize_root(a)
        rb = self._normalize_root(b)
        if ra == rb and len(ra) >= 3:
            return True

        # Proportional prefix overlap
        shared = 0
        for ca, cb in zip(ra, rb):
            if ca == cb:
                shared += 1
            else:
                break
        min_len = min(len(ra), len(rb))
        if min_len >= 4 and shared / min_len >= 0.8:
            return True

        # Edit distance <= 1 on similar-length words
        if abs(len(a) - len(b)) <= 1 and len(a) >= 4:
            diffs = sum(1 for x, y in zip(a, b) if x != y)
            diffs += abs(len(a) - len(b))
            if diffs <= 1:
                return True

        return False

    def _has_overlap(self, words):
        for a, b in combinations(words, 2):
            if self._too_similar_pair(a, b):
                return True
        return False

    def _too_close_to_used(self, word):
        for used in self.seen_words:
            if self._too_similar_pair(word, used):
                return True
        return False

    # ------------------------------------------------------------------
    # Synset quality checks
    # ------------------------------------------------------------------

    def _gloss_too_generic(self, gloss):
        gloss_lower = gloss.lower()
        if len(gloss_lower.split()) < 4:
            return True
        return any(token in gloss_lower for token in self.bad_gloss_words)

    def _valid_synset_words(self, synset):
        if self._gloss_too_generic(synset.definition()):
            return None

        words = []
        seen = set()

        for lemma in synset.lemmas():
            cleaned = self._clean_word(lemma.name())
            if not cleaned or cleaned in seen:
                continue
            if not self._is_good_frequency(cleaned):
                continue
            if cleaned in self.seen_words or self._too_close_to_used(cleaned):
                continue
            seen.add(cleaned)
            words.append(cleaned)

        if len(words) < 4:
            return None

        return words

    # ------------------------------------------------------------------
    # Ambiguity / deceptiveness scoring
    # ------------------------------------------------------------------

    def _get_ambiguity(self, word):
        if word not in self._ambiguity_cache:
            self._ambiguity_cache[word] = len(wn.synsets(word))
        return self._ambiguity_cache[word]

    def _group_score(self, words):
        if self._has_overlap(words):
            return float("-inf")

        ambiguity = sum(min(self._get_ambiguity(w), 10) for w in words)

        freq_bonus = 0.0
        for w in words:
            z = zipf_frequency(word=w, lang="en")
            if 4.0 <= z <= 5.5:
                freq_bonus += 1.5
            elif z > 5.5:
                freq_bonus -= 0.5

        lengths = [len(w) for w in words]
        spread_penalty = (max(lengths) - min(lengths)) * 0.3

        return ambiguity + freq_bonus - spread_penalty

    # ------------------------------------------------------------------
    # Group selection
    # ------------------------------------------------------------------

    def _pick_best_four(self, words):
        if len(words) < 4:
            return None
        if len(words) == 4:
            if self._has_overlap(words):
                return None
            return words

        combos = list(combinations(words, 4))
        if len(combos) > 40:
            combos = random.sample(combos, 40)

        best = None
        best_score = float("-inf")

        for combo in combos:
            combo = list(combo)
            score = self._group_score(combo)
            if score > best_score:
                best_score = score
                best = combo

        return best

    def _is_duplicate_group(self, chosen):
        key = tuple(sorted(chosen))
        if key in self.seen_groups:
            return True
        self.seen_groups.add(key)
        return False

    # ------------------------------------------------------------------
    # Category label generation
    # ------------------------------------------------------------------

    _GLOSS_STRIP_PREFIXES = [
        "a ", "an ", "the ", "any ", "one who ", "one that ",
    ]

    def _make_category_label(self, synset, chosen_words):
        """
        Build a Connections-style category label.

        Priority:
        1. Use a synset lemma that ISN'T one of the 4 answer words
           and isn't morphologically similar to any of them.
           -> e.g. answers = [battle, conflict, fight, engagement]
              synset also has "struggle" -> label = "STRUGGLE"

        2. Clean up the synset definition into a short phrase.
           -> "an angry disturbance" -> "Angry disturbance"

        3. Fallback: "They mean {first_lemma}"
        """
        chosen_set = set(chosen_words)

        # Strategy 1: spare lemma from the synset
        for lemma in synset.lemmas():
            name = lemma.name().replace("_", " ").lower().strip()
            # Allow multi-word labels from lemmas (e.g. "dead body")
            if name in chosen_set:
                continue
            # Single words: check morphological similarity
            if " " not in name:
                if any(self._too_similar_pair(name, w) for w in chosen_words):
                    continue
            return name.upper()

        # Strategy 2: derive from definition
        definition = synset.definition()
        if definition:
            label = definition.strip()
            label_lower = label.lower()
            for prefix in self._GLOSS_STRIP_PREFIXES:
                if label_lower.startswith(prefix):
                    label = label[len(prefix):]
                    break

            # Truncate at first clause boundary
            for delim in [";", ",", " - ", " -- ", " (", " that ", " which "]:
                if delim in label:
                    label = label[: label.index(delim)]
                    break

            words = label.split()
            if len(words) > 6:
                label = " ".join(words[:6])

            if len(label) > 3:
                return label[0].upper() + label[1:]

        # Strategy 3: fallback
        lemma0 = synset.lemmas()[0].name().replace("_", " ").lower()
        return f"They mean {lemma0}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _get_synsets(self):
        if self._synsets is None:
            synsets = []
            for pos in self.pos_options:
                synsets.extend(list(wn.all_synsets(pos=pos)))
            random.shuffle(synsets)
            self._synsets = synsets
        return self._synsets

    def generate(self):
        """
        Return one synonym group, or None if exhausted.

        Uses a cursor to avoid rescanning. Call repeatedly on the
        same instance for guaranteed no word reuse.
        """
        synsets = self._get_synsets()

        while self._cursor < len(synsets):
            synset = synsets[self._cursor]
            self._cursor += 1

            words = self._valid_synset_words(synset)
            if not words:
                continue

            chosen = self._pick_best_four(words)
            if not chosen:
                continue

            if self._is_duplicate_group(chosen):
                continue

            for w in chosen:
                self.seen_words.add(w)

            return {
                "words": chosen,
                "category": self._make_category_label(synset, chosen),
                "meta": {
                    "synset": synset,
                    "definition": synset.definition(),
                },
            }

        return None

    def generate_n(self, n=20):
        results = []
        while len(results) < n:
            group = self.generate()
            if group is None:
                break
            results.append(group)
        return results