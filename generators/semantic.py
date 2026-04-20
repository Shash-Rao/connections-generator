import math
import random
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
import json
import os

import spacy
from nltk.corpus import wordnet as wn
from wordfreq import zipf_frequency


SEED_SUBJECTS = [
    # ANIMALS
    "animals", "mammals", "birds", "fish", "reptiles", "amphibians",
    "insects", "dogs", "cats", "horses", "cattle", "sheep",
    "goats", "pigs", "rabbits", "rodents", "bears", "wolves",
    "foxes", "deer", "whales", "dolphins", "sharks", "snakes",
    "lizards", "frogs", "turtles", "ducks", "geese", "swans",
    "eagles", "hawks", "owls", "parrots", "penguins",

    # FOOD
    "foods", "fruits", "vegetables", "meats", "seafood",
    "cheeses", "breads", "pastries", "desserts", "cakes",
    "cookies", "pies", "pastas", "noodles", "soups",
    "salads", "sandwiches", "sauces", "spices", "herbs",
    "beverages", "drinks", "teas", "coffees", "juices",
    "sodas", "cocktails", "liquors", "wines", "beers",

    # CLOTHING
    "clothing", "shoes", "boots", "sneakers", "sandals",
    "hats", "caps", "jackets", "coats", "shirts",
    "pants", "shorts", "skirts", "dresses", "suits",
    "uniforms", "socks", "gloves", "scarves", "belts",

    # VEHICLES
    "vehicles", "cars", "trucks", "buses", "vans",
    "motorcycles", "bicycles", "trains", "boats",
    "ships", "airplanes", "helicopters", "taxis",
    "ambulances", "wagons", "sedans", "jeeps",
    "limousines", "canoes", "kayaks", "yachts",

    # HOUSEHOLD / OBJECTS
    "furniture", "chairs", "tables", "desks", "beds",
    "lamps", "mirrors", "couches", "sofas", "cabinets",
    "dressers", "wardrobes", "shelves", "appliances",
    "tools", "instruments", "machines", "devices",
    "gadgets", "utensils", "containers", "bottles",
    "jars", "boxes", "bags", "suitcases", "keys",
    "locks", "clocks", "watches", "knives", "forks",
    "spoons", "plates", "cups", "mugs", "bowls",

    # BUILDINGS / PLACES
    "buildings", "houses", "apartments", "rooms",
    "shops", "stores", "schools", "colleges",
    "universities", "churches", "hospitals",
    "offices", "factories", "warehouses",
    "garages", "barns", "cabins", "cottages",
    "mansions", "villas", "lodges", "hotels",
    "restaurants", "cafes", "bakeries",
    "pharmacies", "libraries", "museums",
    "stadiums", "theaters", "airports",

    # PROFESSIONS
    "jobs", "professions", "doctors", "lawyers",
    "scientists", "teachers", "artists", "writers",
    "actors", "musicians", "dancers", "athletes",
    "drivers", "pilots", "engineers", "architects",
    "designers", "builders", "farmers", "chefs",
    "bakers", "detectives", "inspectors",
    "captains", "soldiers", "guards",
    "firefighters", "nurses", "dentists",
    "surgeons", "veterinarians",

    # SPORTS / GAMES
    "sports", "games", "teams", "positions",
    "plays", "moves", "penalties", "trophies",
    "awards", "medals", "ribbons", "prizes",
    "balls", "bats", "rackets", "goals",
    "courts", "tracks", "races", "tournaments",

    # MUSIC / ARTS
    "music", "songs", "dances", "genres",
    "instruments", "bands", "orchestras",
    "choirs", "drums", "guitars", "violins",
    "pianos", "trumpets", "flutes",

    # MEDIA / STORY
    "books", "stories", "novels", "plays",
    "films", "movies", "shows", "series",
    "episodes", "chapters", "scenes",
    "plots", "characters", "heroes", "villains",

    # MATERIALS
    "materials", "metals", "stones", "gems",
    "crystals", "rocks", "minerals", "fabrics",
    "woods", "plastics", "glass", "paper",

    # GEOGRAPHY
    "countries", "states", "cities", "towns",
    "villages", "islands", "continents",
    "oceans", "seas", "rivers", "lakes",
    "mountains", "valleys", "deserts",
    "forests", "jungles", "beaches",

    # TIME
    "times", "hours", "days", "months",
    "years", "decades", "seasons",

    # CLEAN CATEGORY LABELS
    "types", "styles", "models", "brands",
    "categories", "genres", "flavors",
    "colors", "shapes", "sizes",

    # ABSTRACT
    "emotions", "feelings", "beliefs",
    "crimes", "diseases", "injuries",
    "symptoms", "medicines",
]


@dataclass(frozen=True)
class CandidateItem:
    lemma: str
    child_synset: str
    child_depth: int
    freq: float


@dataclass(frozen=True)
class SubjectGroup:
    subject_synset: str
    items: tuple


class SemanticGenerator:
    """
    Key changes from the earlier version:

    1. Preserve child hyponym synset metadata instead of flattening straight to strings.
    2. Clean/editorially filter candidates at the CandidateItem level.
    3. Prevent mixing multiple lemmas from the same child synset.
    4. Prefer sibling-like candidates with similar child depths.
    5. Use subject-synset-aware validation only where it adds value.
    6. Keep difficulty scoring, but separate it from category-validity checks.
    """

    MIN_FREQ = 4.0
    CANDIDATE_MIN_FREQ = 3.0
    MIN_LENGTH = 3
    EXPANSION_DEPTH = 7

    MIN_HYPONYMS = 3
    CATEGORY_SIZE = 4
    TOP_K_HYPONYMS = 12

    MAX_CATEGORIES_PER_SUBJECT = 2
    KEEP_TOP_PERCENT = 0.3

    LABEL_SIM_MIN = 0.43
    MAX_CHILD_DEPTH_RANGE = 4
    MAX_WORD_POLYSEMY = 12

    GENERIC_WORDS = {
        "thing", "item", "part", "stuff",
        "element", "component", "unit", "piece"
    }

    GENERIC_HYPERNYMS = {
        "entity", "physical_entity", "object", "whole", "artifact",
        "abstraction", "attribute", "group", "relation", "act",
        "event", "state", "matter", "psychological_feature",
        "causal_agent", "person", "location", "shape"
    }

    BAD_SUFFIXES = (
        "tion", "sion", "ment", "ness", "ity", "ship", "ism"
    )

    BANNED_WORDS = {
        "oriental", "sex"
    }

    # Subjects that are technically workable in WordNet but tend to yield
    # editorially weak or mixed-type categories for puzzle generation.
    SUBJECT_BLACKLIST = {
        "belief", "beliefs",
        "feeling", "feelings",
        "medicine",  # broad academic/practice sense
        "biology",   # broad academic-field sense
    }

    # Subjects that are allowed, but should be treated cautiously when exporting.
    SUBJECT_DOWNWEIGHT = {
        "wood", "woods",
        "fur", "gas",
    }

    def __init__(self, seeds):
        self.seeds = seeds
        self.nlp = spacy.load("en_core_web_lg", disable=["parser", "ner"])

    # -------------------------
    # NLP CACHE
    # -------------------------

    @lru_cache(maxsize=None)
    def get_doc(self, word):
        return self.nlp(word)

    @lru_cache(maxsize=None)
    def get_vector(self, word):
        doc = self.get_doc(word)
        if not doc.has_vector:
            return None
        return (doc.vector, doc.vector_norm)

    def cosine_sim(self, v1, v2):
        return v1[0].dot(v2[0]) / (v1[1] * v2[1] + 1e-8)

    def pairwise_sims(self, words):
        vecs = [self.get_vector(w) for w in words]
        vecs = [v for v in vecs if v is not None]

        sims = []
        for i in range(len(vecs)):
            for j in range(i + 1, len(vecs)):
                sims.append(self.cosine_sim(vecs[i], vecs[j]))
        return sims

    # -------------------------
    # WORDNET CACHE
    # -------------------------

    @lru_cache(maxsize=None)
    def get_synsets(self, word):
        return wn.synsets(word, pos=wn.NOUN)

    @lru_cache(maxsize=None)
    def synset_by_name(self, name):
        return wn.synset(name)

    @lru_cache(maxsize=None)
    def get_hyponyms(self, word):
        results = set()
        for syn in self.get_synsets(word):
            for h in syn.hyponyms():
                for lemma in h.lemmas():
                    name = lemma.name().lower()
                    if name.isalpha() and "_" not in name:
                        results.add(name)
        return tuple(results)

    @lru_cache(maxsize=None)
    def get_hypernyms(self, word):
        return {
            h.name().split(".")[0]
            for syn in self.get_synsets(word)
            for h in syn.hypernyms()
        }

    @lru_cache(maxsize=None)
    def hypernym_depth(self, word):
        return max((s.max_depth() for s in self.get_synsets(word)), default=0)

    @lru_cache(maxsize=None)
    def get_synset_forms(self, word):
        return {
            lemma.name().lower()
            for syn in self.get_synsets(word)
            for lemma in syn.lemmas()
        }

    @lru_cache(maxsize=None)
    def get_hypernym_closure_by_name(self, synset_name):
        syn = self.synset_by_name(synset_name)
        closure = set()
        for path in syn.hypernym_paths():
            for node in path:
                closure.add(node.name().split(".")[0])
        return closure

    @lru_cache(maxsize=None)
    def word_polysemy(self, word):
        return len(self.get_synsets(word))

    # -------------------------
    # BASIC VALIDATION
    # -------------------------

    def is_valid_word(self, word):
        return len(word) >= 3 and self.get_vector(word) is not None

    def is_candidate_subject(self, word):
        return (
            len(word) >= self.MIN_LENGTH
            and word.isalpha()
            and zipf_frequency(word, "en") >= self.CANDIDATE_MIN_FREQ
            and len(self.get_hyponyms(word)) >= 2
        )

    def is_valid_subject(self, word):
        return (
            word not in self.SUBJECT_BLACKLIST
            and zipf_frequency(word, "en") >= self.MIN_FREQ
            and len(self.get_hyponyms(word)) >= self.MIN_HYPONYMS
            and self.hypernym_depth(word) >= 4
        )

    # -------------------------
    # SUBJECT GENERATION
    # -------------------------

    def generate_subjects(self):
        candidates = {s for s in self.seeds if self.is_candidate_subject(s)}

        for _ in range(self.EXPANSION_DEPTH):
            new = set()
            for word in candidates:
                for syn in self.get_synsets(word):
                    for rel in syn.hypernyms() + syn.hyponyms():
                        for lemma in rel.lemmas():
                            t = lemma.name().lower()
                            if t.isalpha() and self.is_candidate_subject(t):
                                new.add(t)
            candidates |= new

        return [w for w in candidates if self.is_valid_subject(w)]

    # -------------------------
    # CANDIDATE CONCEPT EXTRACTION
    # -------------------------

    def candidate_item_from_child_synset(self, child_synset):
        items = []
        child_name = child_synset.name()
        child_depth = child_synset.max_depth()

        for lemma in child_synset.lemmas():
            word = lemma.name().lower()
            if not word.isalpha() or "_" in word:
                continue
            if word in self.BANNED_WORDS:
                continue
            items.append(
                CandidateItem(
                    lemma=word,
                    child_synset=child_name,
                    child_depth=child_depth,
                    freq=zipf_frequency(word, "en"),
                )
            )
        return items

    @lru_cache(maxsize=None)
    def get_hyponym_groups(self, subject_word):
        groups = []

        for subject_synset in self.get_synsets(subject_word):
            items = []
            for child in subject_synset.hyponyms():
                items.extend(self.candidate_item_from_child_synset(child))

            if len(items) >= 4:
                groups.append(
                    SubjectGroup(
                        subject_synset=subject_synset.name(),
                        items=tuple(items),
                    )
                )

        return tuple(groups)

    # -------------------------
    # EDITORIAL FILTERING
    # -------------------------

    def looks_too_abstract(self, word):
        return word.endswith(self.BAD_SUFFIXES)

    def noun_strength(self, words):
        return sum(
            1 for w in words
            if all(t.pos_ == "NOUN" for t in self.get_doc(w))
        ) / len(words)

    def same_level_enough(self, items):
        depths = [item.child_depth for item in items]
        return max(depths) - min(depths) <= self.MAX_CHILD_DEPTH_RANGE

    def child_synset_overlap_ok(self, items):
        synsets = [item.child_synset for item in items]
        return len(set(synsets)) == len(synsets)

    def surface_overlap_ok(self, subject, words):
        if any(word == subject for word in words):
            return False
        if any(word in subject for word in words):
            return False
        if any(subject in word for word in words):
            return False
        return True

    def shared_specific_hypernyms(self, words):
        closures = []
        for word in words:
            word_closure = set()
            for syn in self.get_synsets(word):
                for path in syn.hypernym_paths():
                    for node in path:
                        word_closure.add(node.name().split(".")[0])
            closures.append(word_closure)

        if not closures:
            return set()

        shared = set.intersection(*closures)
        return {h for h in shared if h not in self.GENERIC_HYPERNYMS}

    def clean_group(self, subject, subject_group):
        seen_lemmas = set()
        seen_synset_forms = set()
        filtered = []
        seen_prefix = set()
        seen_suffix = set()

        # Prefer common, concrete surface forms from each child node.
        ordered = sorted(subject_group.items, key=lambda item: (-item.freq, item.lemma))

        for item in ordered:
            word = item.lemma

            if item.freq < 3.0:
                continue
            if word[:3] in seen_prefix or word[-3:] in seen_suffix:
                continue
            if not self.is_valid_word(word):
                continue
            if self.word_polysemy(word) > self.MAX_WORD_POLYSEMY:
                continue
            if self.looks_too_abstract(word):
                continue
            if word in seen_lemmas:
                continue
            if not all(t.pos_ == "NOUN" for t in self.get_doc(word)):
                continue

            forms = self.get_synset_forms(word)
            if seen_synset_forms & forms:
                continue

            seen_lemmas.add(word)
            seen_synset_forms |= forms
            filtered.append(item)
            seen_prefix.add(word[:3])
            seen_suffix.add(word[-3:])

        # Keep top-k candidate items, but preserve concept metadata.
        filtered = filtered[:self.TOP_K_HYPONYMS]

        if len(filtered) < self.CATEGORY_SIZE:
            return []

        return filtered

    # -------------------------
    # LABEL / COHESION SIGNALS
    # -------------------------

    def label_similarity(self, subject, words):
        label_vec = self.get_vector(subject)
        if not label_vec:
            return 0.0

        sims = []
        for word in words:
            word_vec = self.get_vector(word)
            if word_vec is None:
                continue
            sims.append(self.cosine_sim(label_vec, word_vec))

        return sum(sims) / len(sims) if sims else 0.0

    def average_frequency(self, words):
        freqs = [zipf_frequency(w, "en") for w in words]
        return sum(freqs) / len(freqs) if freqs else 0.0

    def canonical_obviousness(self, subject, words, items):
        """
        Override signal for categories that are clearly canonical / textbook lists,
        even if polysemy nudges the difficulty score upward.
        """
        sims = self.pairwise_sims(words)
        if not sims:
            return 0.0

        avg_sim = sum(sims) / len(sims)
        var = max(sims) - min(sims)
        label_score = self.label_similarity(subject, words)
        avg_freq = self.average_frequency(words)
        depth_range = max(item.child_depth for item in items) - min(item.child_depth for item in items)

        bonus = 0.0
        if label_score >= 0.62:
            bonus += 0.4
        if avg_sim >= 0.42:
            bonus += 0.25
        if var <= 0.22:
            bonus += 0.2
        if avg_freq >= 4.2:
            bonus += 0.15
        if depth_range <= 1:
            bonus += 0.15

        return bonus

    def shared_hypernym_ratio(self, words):
        sets = [self.get_hypernyms(w) for w in words]
        if not sets:
            return 0.0
        shared = set.intersection(*sets)
        total = set.union(*sets)
        return len(shared) / len(total) if total else 0.0

    # -------------------------
    # SAME-TYPE VALIDATION
    # -------------------------

    def score_candidate_validity(self, subject, items):
        words = tuple(item.lemma for item in items)

        if any(w in self.GENERIC_WORDS for w in words):
            return -1.0
        if not self.surface_overlap_ok(subject, words):
            return -1.0
        if not self.child_synset_overlap_ok(items):
            return -1.0
        if not self.same_level_enough(items):
            return -1.0
        if self.noun_strength(words) < 1.0:
            return -1.0
        if not self.shared_specific_hypernyms(words):
            return -1.0

        sims = self.pairwise_sims(words)
        if not sims:
            return -1.0

        avg_sim = sum(sims) / len(sims)
        var = max(sims) - min(sims)
        label_score = self.label_similarity(subject, words)
        hyper_ratio = self.shared_hypernym_ratio(words)

        if label_score < self.LABEL_SIM_MIN:
            return -1.0

        return (
            avg_sim * 2.5
            + hyper_ratio * 2.0
            + label_score * 2.5
            - var * 2.5
        )

    # -------------------------
    # DIFFICULTY
    # -------------------------

    def compute_difficulty(self, subject, words, items=None):
        polys = [self.word_polysemy(w) for w in words]
        avg_poly = sum(polys) / len(polys)
        max_poly = max(polys)
        poly_score = 0.7 * avg_poly + 0.3 * max_poly
        poly_score = math.log(1 + poly_score)

        label_score = self.label_similarity(subject, words)
        difficulty_clarity = 1 - label_score

        sims = self.pairwise_sims(words)
        if not sims:
            return None

        avg_sim = sum(sims) / len(sims)
        var = max(sims) - min(sims)
        cohesion = avg_sim - var
        difficulty_cohesion = 1 - cohesion

        avg_freq = self.average_frequency(words)
        difficulty_freq = max(0, 5.5 - avg_freq)

        difficulty = (
            poly_score * 0.50
            + difficulty_clarity * 0.25
            + difficulty_cohesion * 0.15
            + difficulty_freq * 0.10
        )

        if items is not None:
            difficulty -= self.canonical_obviousness(subject, words, items) * 0.22

        if subject in self.SUBJECT_DOWNWEIGHT:
            difficulty += 0.08

        return difficulty

    def assign_level(self, difficulty):
        if difficulty is None:
            return None
        return "green" if difficulty < 1.05 else "blue"

    # -------------------------
    # CATEGORY GENERATION
    # -------------------------

    def generate_categories_from_subject(self, subject):
        categories = []

        for subject_group in self.get_hyponym_groups(subject):
            cleaned_items = self.clean_group(subject, subject_group)
            if len(cleaned_items) < self.CATEGORY_SIZE:
                continue

            for combo_items in combinations(cleaned_items, self.CATEGORY_SIZE):
                score = self.score_candidate_validity(subject, combo_items)
                if score <= 0:
                    continue

                words = tuple(item.lemma for item in combo_items)
                difficulty = self.compute_difficulty(subject, words, combo_items)
                level = self.assign_level(difficulty)

                categories.append({
                    "subject": subject,
                    "words": words,
                    "score": score,
                    "difficulty": difficulty,
                    "level": level,
                    "subject_synset": subject_group.subject_synset,
                    "child_synsets": tuple(item.child_synset for item in combo_items),
                })

                if len(categories) >= self.MAX_CATEGORIES_PER_SUBJECT:
                    return categories

        return categories

    def generate_all_categories(self):
        all_categories = []

        for subject in self.generate_subjects():
            all_categories.extend(self.generate_categories_from_subject(subject))

        all_categories.sort(key=lambda x: x["score"], reverse=True)
        cutoff = int(len(all_categories) * self.KEEP_TOP_PERCENT)
        return all_categories[:cutoff]
    
    def generate_json(self, output_path="categories/semantic.json"):
        categories = self.generate_all_categories()

        json_data = []

        for cat in categories:
            json_data.append({
                "category_name": cat["subject"],
                "words": list(cat["words"]),
                "category_type": "semantic",
                "difficulty": cat["level"]
            })

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"\nSaved {len(json_data)} categories to {output_path}\n")

        return json_data


if __name__ == "__main__":
    generator = SemanticGenerator(SEED_SUBJECTS)
    generator.generate_json()

    # categories = generator.generate_all_categories()

    # print(f"\nGenerated {len(categories)} categories\n")

    # random.shuffle(categories)
    # for c in categories[:100]:
    #     print(c)
