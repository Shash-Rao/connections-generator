import random
import re
from itertools import combinations
from nltk.corpus import wordnet as wn
from wordfreq import zipf_frequency
import json
import os


class SynonymGenerator:
    """
    Generates Connections-style synonym groups from WordNet.
    Two strategies:
      - synonym: words from a single synset (pure synonyms)
      - cross_synset: one word per hyponym of a shared hypernym (thematic groups)
    """

    def __init__(self, enforce_global_dedup=False, combo_sample_limit=100):
        self.enforce_global_dedup = enforce_global_dedup
        self.combo_sample_limit = combo_sample_limit

        self.min_zipf = 2.8
        self.max_zipf = 6.5

        self.pos_options = [wn.ADJ, wn.NOUN, wn.VERB, wn.ADV]

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

        # Lowercase proper nouns that slip through (names used as common words in WordNet)
        self.bad_words_extra = {"ira", "ada", "eli", "abe", "ima"}

        self.profanity = {
            "shit", "fuck", "cunt", "cock", "dick", "prick", "ass", "arse",
            "bitch", "bastard", "piss", "crap", "slut", "whore", "retard",
            "faggot", "nigger", "chink", "spic", "kike", "twat", "wank",
            "wanker", "tosser", "bollocks", "bugger", "sob", "turd",
            "screw", "bang", "bonk", "shag", "hump", "bed",
        }

        # WordNet synset name patterns that are technical/ugly and should never
        # be shown as category labels. Checked against the raw synset name.
        self._ugly_name_patterns = re.compile(
            r"(musteline|gramineous|cartilaginous|salmonid|"
            r"oscine|anseriform|passerine|percoid|acarine|"
            r"bovid|cervid|ungulate|pinniped|marsupial|"
            r"placental|eutherian|metatherian|chordate|"
            r"liquid_body|solid_body|gaseous|"
            r"humanistic_discipline|natural_philosophy|"
            r"cognitive_content|cognitive_state|"
            r"physical_entity|causal_agent|causal_agency|"
            r"self_propelled|wheeled_vehicle|motor_vehicle|"
            r"ratite|columbiform|galliform|"
            r"bodily_process|bodily_property|"
            r"psychological_feature|abstraction|"
            r"_phenomenon|_process|_property|_state|"
            r"_agent|_entity|_feature|_content)",
            re.IGNORECASE,
        )

        self.seen_groups = set()
        self.seen_words = set()

        self._ambiguity_cache = {}
        self._synsets = None
        self._cursor = 0

        self._cross_synsets = None
        self._cross_cursor = 0

    # ------------------------------------------------------------------
    # Word cleaning & validation
    # ------------------------------------------------------------------

    def _clean_word(self, word):
        # Reject proper nouns — WordNet lemma names starting uppercase are names
        if word and word[0].isupper():
            return None
        word = word.replace("_", " ").lower().strip()
        if " " in word or "-" in word:
            return None
        if len(word) < 3 or len(word) > 13:
            return None
        if not word.isalpha():
            return None
        if word in self.bad_words:
            return None
        if word in self.profanity:
            return None
        if word in self.bad_words_extra:
            return None
        return word

    def _is_good_frequency(self, word):
        z = zipf_frequency(word, "en")
        return self.min_zipf <= z <= self.max_zipf

    # ------------------------------------------------------------------
    # Morphological / spelling similarity detection
    # ------------------------------------------------------------------

    _SPELLING_NORMALIZATIONS = [
        ("our", "or"), ("ise", "ize"), ("isation", "ization"),
        ("yse", "yze"), ("ogue", "og"), ("ence", "ense"),
        ("ae", "e"), ("oe", "e"), ("grey", "gray"),
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
            "er", "ed", "ly", "al", "en", "es", "or", "ty", "s",
        ]
        root = word
        for suffix in suffixes:
            if len(root) > len(suffix) + 2 and root.endswith(suffix):
                root = root[:-3] + "y" if suffix == "ies" else root[:-len(suffix)]
                break
        return root

    def _too_similar_pair(self, a, b):
        if a == b or a in b or b in a:
            return True
        if self._normalize_spelling(a) == self._normalize_spelling(b):
            return True
        ra, rb = self._normalize_root(a), self._normalize_root(b)
        if ra == rb and len(ra) >= 3:
            return True
        shared = 0
        for ca, cb in zip(ra, rb):
            if ca == cb:
                shared += 1
            else:
                break
        min_len = min(len(ra), len(rb))
        if min_len >= 4 and shared / min_len >= 0.7:
            return True
        if abs(len(a) - len(b)) <= 1 and len(a) >= 4:
            diffs = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
            if diffs <= 1:
                return True
        return False

    def _has_overlap(self, words):
        return any(self._too_similar_pair(a, b) for a, b in combinations(words, 2))

    def _too_close_to_used(self, word):
        return any(self._too_similar_pair(word, used) for used in self.seen_words)

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
        words, seen = [], set()
        for lemma in synset.lemmas():
            cleaned = self._clean_word(lemma.name())
            if not cleaned or cleaned in seen:
                continue
            if not self._is_good_frequency(cleaned):
                continue
            if self.enforce_global_dedup:
                if cleaned in self.seen_words or self._too_close_to_used(cleaned):
                    continue
            seen.add(cleaned)
            words.append(cleaned)
        return words if len(words) >= 4 else None

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
        freq_bonus = sum(
            1.5 if 4.0 <= zipf_frequency(w, "en") <= 5.5
            else -0.5 if zipf_frequency(w, "en") > 5.5 else 0
            for w in words
        )
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
            return None if self._has_overlap(words) else words
        combos = list(combinations(words, 4))
        if len(combos) > self.combo_sample_limit:
            combos = random.sample(combos, self.combo_sample_limit)
        best, best_score = None, float("-inf")
        for combo in combos:
            combo = list(combo)
            s = self._group_score(combo)
            if s > best_score:
                best_score, best = s, combo
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

    # Prefixes to strip from definitions before using as labels
    _LABEL_PREFIXES = [
        "a ", "an ", "the ", "any ", "one who ", "one that ",
        "being ", "having ", "making ", "used ", "of ", "or ",
        "and ", "to ", "in ", "not ", "with ",
        "characterized by ", "marked by ", "filled with ",
        "relating to ", "pertaining to ", "expressing ",
        "showing ", "involving ", "denoting ", "describing ",
        "referring to ", "used to ", "used for ",
    ]

    # Delimiters to cut the definition at
    _LABEL_DELIMITERS = ["; ", ", ", " - ", " -- ", " (", " that ",
                         " which ", " or ", " e.g.", ":", " especially",
                         " usually ", " typically ", " when ", " as in "]

    def _is_ugly_synset_name(self, name):
        """Returns True for technical WordNet internal names like MUSTELINE_MAMMAL."""
        # Multi-word names joined by underscores that are jargon
        if "_" in name and self._ugly_name_patterns.search(name):
            return True
        # 3+ part underscore names are always jargon (e.g. self_propelled_vehicle)
        parts = name.split("_")
        if len(parts) >= 3:
            return True
        return False

    def _clean_definition_label(self, definition):
        """Turn a WordNet definition into a short clean label. Returns None if can't."""
        label = definition.strip()
        label_lower = label.lower()

        # Drop parenthetical-start definitions like "(of ..." or "(used ..."
        if label_lower.startswith("("):
            return None

        # Strip leading filler words, up to 4 passes for stacked prefixes
        for _ in range(4):
            stripped = False
            for prefix in self._LABEL_PREFIXES:
                if label_lower.startswith(prefix):
                    label = label[len(prefix):]
                    label_lower = label.lower()
                    stripped = True
                    break
            if not stripped:
                break

        # Cut at first natural break
        for delim in self._LABEL_DELIMITERS:
            if delim in label:
                label = label[: label.index(delim)]
                break

        # Hard cap at 3 words for readability
        words = label.split()
        if len(words) > 3:
            label = " ".join(words[:3])

        # Must be at least 2 meaningful words
        if len(label.split()) < 2:
            return None

        # Reject if last word is a dangling preposition/conjunction/article
        # e.g. "Belligerence aroused by" or "Crime less serious than"
        _dangling = {
            "a", "an", "the", "by", "of", "in", "to", "at",
            "on", "or", "and", "for", "nor", "but", "yet",
            "so", "as", "than", "with", "from", "into",
            "most", "more", "very", "its", "their", "some",
            "this", "that", "such", "also", "well",
        }
        last_word = label.split()[-1].lower().rstrip(".,;:")
        if last_word in _dangling:
            return None

        # Also reject if the label is clearly just the start of a longer
        # definition phrase — detected by ending with an adjective modifier
        # when the full definition has 8+ words (we got cut too early)
        definition_words = definition.split()
        label_words = label.split()
        if len(definition_words) >= 8 and len(label_words) <= 3:
            # Short label from long definition — only keep if it reads
            # as a complete noun phrase (ends with a noun-like word)
            _weak_endings = {
                "sudden", "violent", "serious", "extreme",
                "important", "significant", "certain", "special",
                "particular", "general", "common", "various",
                "different", "similar", "additional", "potential",
                "further", "initial", "final", "several",
                "signifying", "aroused", "established",
                "unconstrained", "unpredictable", "abundant",
            }
            if last_word in _weak_endings:
                return None

        return label[0].upper() + label[1:]

    def _make_category_label(self, synset, chosen_words):
        chosen_set = set(chosen_words)

        # Try every lemma — use the first one that is clean and not in chosen words
        for lemma in synset.lemmas():
            raw = lemma.name()
            name = raw.replace("_", " ").lower().strip()

            # Skip if it contains non-alpha chars (numbers, symbols)
            if not all(c.isalpha() or c == " " for c in name):
                continue

            # Skip if word or phrase is in the chosen set
            if name in chosen_set:
                continue

            # Skip single words too similar to a chosen word
            if " " not in name and any(
                self._too_similar_pair(name, w) for w in chosen_words
            ):
                continue

            # Skip if the lemma name itself is ugly jargon
            # (matches our pattern list — e.g. musteline_mammal, causal_agent)
            if self._ugly_name_patterns.search(raw):
                continue

            return name.upper()

        # No clean lemma found — fall back to cleaned definition
        definition = synset.definition()
        if definition:
            label = self._clean_definition_label(definition)
            if label:
                return label.upper()

        # Absolute last resort
        return synset.lemmas()[0].name().replace("_", " ").upper()

    # ------------------------------------------------------------------
    # Cross-synset strategy (one word per hyponym of a shared hypernym)
    # ------------------------------------------------------------------

    def _get_cross_synsets(self):
        if self._cross_synsets is None:
            hypernyms = []
            for pos in [wn.NOUN, wn.VERB]:
                hypernyms.extend(list(wn.all_synsets(pos=pos)))
            random.shuffle(hypernyms)
            self._cross_synsets = hypernyms
        return self._cross_synsets

    def _words_from_hyponyms(self, hypernym_synset):
        candidates = []
        for hypo in hypernym_synset.hyponyms():
            for lemma in hypo.lemmas():
                w = self._clean_word(lemma.name())
                if w and self._is_good_frequency(w):
                    if not (self.enforce_global_dedup and (
                        w in self.seen_words or self._too_close_to_used(w)
                    )):
                        candidates.append(w)
                        break
        return candidates

    def generate_cross_synset(self):
        synsets = self._get_cross_synsets()

        while self._cross_cursor < len(synsets):
            synset = synsets[self._cross_cursor]
            self._cross_cursor += 1

            defn = synset.definition()
            if not defn or len(defn.split()) < 3:
                continue

            words = self._words_from_hyponyms(synset)
            if not words or len(words) < 4:
                continue

            chosen = self._pick_best_four(words)
            if not chosen:
                continue

            if self._is_duplicate_group(chosen):
                continue

            if self.enforce_global_dedup:
                for w in chosen:
                    self.seen_words.add(w)

            return {
                "words": chosen,
                "category": self._make_category_label(synset, chosen),
                "meta": {
                    "synset": synset,
                    "definition": defn,
                    "type": "cross_synset",
                },
            }

        return None

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

            if self.enforce_global_dedup:
                for w in chosen:
                    self.seen_words.add(w)

            return {
                "words": chosen,
                "category": self._make_category_label(synset, chosen),
                "meta": {
                    "synset": synset,
                    "definition": synset.definition(),
                    "type": "synonym",
                },
            }
        return None

    def generate_n(self, n=20):
        results = []
        synonym_exhausted = False
        cross_exhausted = False

        while len(results) < n:
            if synonym_exhausted and cross_exhausted:
                break

            # Alternate one synonym, one cross_synset
            if not synonym_exhausted:
                group = self.generate()
                if group is None:
                    synonym_exhausted = True
                else:
                    results.append(group)
                    if len(results) >= n:
                        break

            if not cross_exhausted:
                group = self.generate_cross_synset()
                if group is None:
                    cross_exhausted = True
                else:
                    results.append(group)

        return results

    def generate_json(self, n=500, output_path="categories/synonym.json"):
        categories = self.generate_n(n)

        json_data = []

        for cat in categories:
            json_data.append({
                "category_name": "Synonyms for " + cat["category"].lower(),
                "words": list(cat["words"]),
                "category_type": "synonym",
                "difficulty": "yellow"
            })

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"\nSaved {len(json_data)} categories to {output_path}\n")

        return json_data

if __name__ == "__main__":
    generator = SynonymGenerator()
    generator.generate_json()