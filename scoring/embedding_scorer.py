import numpy as np
from wordfreq import zipf_frequency
from utils.embeddings import get_model
from nltk.corpus import wordnet as wn

GENERIC_WORDS = {
    "thing", "stuff", "item", "good", "bad", "part", "piece", "type"
}


# -----------------------
# BASIC UTILS
# -----------------------

def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


_synset_cache = {}

def get_synsets(words, category_syn):
    """
    Resolve each word to its best synset relative to category_syn.
    Tries all POS, not just nouns. Results are cached per (word, synset).
    """
    synsets = []
    for w in words:
        cache_key = (w, category_syn.name())
        if cache_key in _synset_cache:
            result = _synset_cache[cache_key]
            if result is None:
                return None
            synsets.append(result)
            continue

        candidates = wn.synsets(w)
        if not candidates:
            _synset_cache[cache_key] = None
            return None
        scored = [(s.path_similarity(category_syn) or 0, s) for s in candidates]
        best_score, best_syn = max(scored, key=lambda x: x[0])
        result = best_syn if best_score > 0 else candidates[0]
        _synset_cache[cache_key] = result
        synsets.append(result)
    return synsets


# -----------------------
# SCORING COMPONENTS (shared)
# -----------------------

def cluster_tightness(words, model):
    vectors = [model[w] for w in words if w in model]
    if len(vectors) < 2:
        return 0.0
    centroid = np.mean(vectors, axis=0)
    return float(np.mean([cosine_sim(v, centroid) for v in vectors]))


def min_similarity(words, model):
    vectors = [model[w] for w in words if w in model]
    if len(vectors) < 2:
        return 0.0
    sims = [
        cosine_sim(vectors[i], vectors[j])
        for i in range(len(vectors))
        for j in range(i + 1, len(vectors))
    ]
    return min(sims)


def avg_frequency(words):
    return sum(zipf_frequency(w, "en") for w in words) / len(words)


def category_alignment(words, category_syn, synsets):
    if not synsets:
        return 0.0
    return sum(
        any(category_syn in path for path in s.hypernym_paths())
        for s in synsets
    ) / len(synsets)


# -----------------------
# HARD FILTERS
# -----------------------

def _base_checks(words, model):
    """Checks that apply to all group types."""
    if any(len(w) < 2 for w in words):
        return False
    if any(w not in model for w in words):
        return False
    if any(zipf_frequency(w, "en") < 2.5 for w in words):
        return False
    return True


def is_valid_synonym_group(words, model, category_syn):
    """Stricter validation for within-synset synonym groups."""
    if not _base_checks(words, model):
        return False
    synsets = get_synsets(words, category_syn)
    if not synsets:
        return False
    if cluster_tightness(words, model) < 0.65:
        return False
    return True


def is_valid_cross_synset_group(words, model):
    """
    Validation for cross-synset groups.
    Words come from different synsets by design, so we skip synset-based
    checks and rely on embedding coherence alone. Threshold set at 0.60
    to filter weak groups like [wind, stay, shine, cover] under BE.
    """
    if not _base_checks(words, model):
        return False
    if cluster_tightness(words, model) < 0.55:
        return False
    # Minimum pairwise similarity catches outlier words
    if min_similarity(words, model) < 0.20:
        return False
    return True


# -----------------------
# MAIN SCORE FUNCTION
# -----------------------

def score(group):
    if group.get("meta", {}).get("type") == "anagram":
        return anagram_score(group)
    
    model = get_model()
    words = group["words"]
    group_type = group["meta"].get("type", "synonym")

    if group_type == "cross_synset":
        if not is_valid_cross_synset_group(words, model):
            return float("-inf")
    else:
        category_syn = group["meta"]["synset"]
        if not is_valid_synonym_group(words, model, category_syn):
            return float("-inf")

    return (
        cluster_tightness(words, model) +
        min_similarity(words, model) +
        0.5 * avg_frequency(words)
    )

def anagram_score(group):
    words = group["words"]

    # reward longer words (harder puzzles)
    avg_len = sum(len(w) for w in words) / len(words)

    # reward diversity in frequency (less trivial)
    freqs = [zipf_frequency(w, "en") for w in words]
    freq_var = max(freqs) - min(freqs)

    return avg_len + 0.5 * freq_var