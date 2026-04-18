import numpy as np
from nltk.corpus import wordnet as wn
from scoring.embedding_scorer import (
    get_synsets,
    cluster_tightness,
    avg_frequency,
    category_alignment,
)
from utils.embeddings import get_model

# -----------------------
# CORE SIGNALS
# -----------------------

def ambiguity_score(words):
    """
    Average number of WordNet senses per word.
    Higher = more ambiguous = harder.
    """
    counts = [len(wn.synsets(w)) for w in words]
    return sum(counts) / len(counts)


def difficulty_score(group):
    """
    Continuous difficulty score.
    Higher = harder.
    """

    if group.get("meta", {}).get("type") == "anagram":
        return anagram_difficulty(group)

    model = get_model()

    words = group["words"]
    syn = group["meta"]["synset"]
    synset = get_synsets(words, syn)

    tightness = cluster_tightness(words, model)
    alignment = category_alignment(words, syn, synset)
    ambiguity = ambiguity_score(words)
    freq = avg_frequency(words)

    return (
        -2.0 * tightness +     # less cohesive = harder
        -1.5 * alignment +     # less category fit = harder
        10.0 * ambiguity +      # more meanings = harder
        -1.0 * freq            # rarer words = harder
    )


# -----------------------
# BUCKETING
# -----------------------

def compute_percentiles(groups):
    """
    Compute difficulty percentiles for a batch of groups.
    """
    scores = [difficulty_score(g) for g in groups]

    p25, p50, p75 = np.percentile(scores, [25, 50, 75])

    return p25, p50, p75


def difficulty_label(score, p25, p50, p75):
    """
    Map score to 2 difficulty tiers.
    """
    if score <= p50:
        return "easy"      # green
    else:
        return "medium"   # purple


def assign_difficulties(groups):
    """
    Annotate groups with difficulty scores + labels.
    """
    p25, p50, p75 = compute_percentiles(groups)

    for g in groups:
        s = difficulty_score(g)
        g["difficulty_score"] = s
        g["difficulty"] = difficulty_label(s, p25, p50, p75)

    return groups

def anagram_difficulty(group):
    words = group["words"]

    # longer words = harder
    avg_len = sum(len(w) for w in words) / len(words)

    # optional: add frequency difficulty
    from wordfreq import zipf_frequency
    avg_freq = sum(zipf_frequency(w, "en") for w in words) / len(words)

    return avg_len - 0.5 * avg_freq