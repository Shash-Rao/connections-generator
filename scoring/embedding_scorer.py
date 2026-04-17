import numpy as np
from wordfreq import zipf_frequency
from utils.embeddings import get_model
from nltk.corpus import wordnet as wn

'''

GENERIC_WORDS = {
    "thing", "stuff", "item", "good", "bad", "part", "piece", "type"
}

def get_pos(word):
    synsets = wn.synsets(word)
    if not synsets:
        return None
    return synsets[0].pos()

def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def generic_penalty(words):
    return sum(1 for w in words if w in GENERIC_WORDS)

def stem_penalty(words):
    stems = [w.rstrip("ing").rstrip("ed").rstrip("s") for w in words]
    return len(stems) - len(set(stems))

def pos_consistency(words):
    poses = [get_pos(w) for w in words]
    
    poses = [p for p in poses if p is not None]

    if not poses:
        return 0

    most_common = max(set(poses), key=poses.count)
    count = poses.count(most_common)

    return count / len(poses)

def cluster_tightness(words, model):
    vectors = [model[w] for w in words if w in model]

    if len(vectors) < 2:
        return 0

    centroid = np.mean(vectors, axis=0)

    sims = [cosine_sim(v, centroid) for v in vectors]
    return sum(sims) / len(sims)


def redundancy_penalty(words, model, threshold=0.75):
    vectors = [model[w] for w in words if w in model]

    penalty = 0

    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            if cosine_sim(vectors[i], vectors[j]) > threshold:
                penalty += 1

    return penalty


def avg_frequency(words):
    return sum(zipf_frequency(w, "en") for w in words) / len(words)

def best_synset_for_word(word, category_syn):
    synsets = wn.synsets(word, pos='n')

    best = None
    best_score = -1

    for s in synsets:
        sim = s.path_similarity(category_syn) or 0
        if sim > best_score:
            best_score = sim
            best = s

    return best


def share_hypernym(words, category_syn):
    synsets = []

    for w in words:
        s = best_synset_for_word(w, category_syn)
        if not s:
            return False
        synsets.append(s)

    hypernym_sets = [set(s.hypernyms()) for s in synsets]

    common = set.intersection(*hypernym_sets)

    return len(common) > 0


def same_lexname(words, category_syn):
    synsets = []

    for w in words:
        s = best_synset_for_word(w, category_syn)
        if not s:
            return False
        synsets.append(s)

    lexnames = [s.lexname() for s in synsets]

    return len(set(lexnames)) == 1


def category_alignment(words, category_syn):
    synsets = []

    for w in words:
        s = best_synset_for_word(w, category_syn)
        if not s:
            return 0
        synsets.append(s)

    score = 0

    for s in synsets:
        paths = s.hypernym_paths()
        if any(category_syn in path for path in paths):
            score += 1

    return score / len(words)

def min_similarity_to_centroid(words, model):
    vectors = [model[w] for w in words if w in model]

    if len(vectors) < 2:
        return 0

    centroid = np.mean(vectors, axis=0)

    sims = [cosine_sim(v, centroid) for v in vectors]

    return min(sims)

def min_wordnet_similarity(words, category_syn):
    synsets = [best_synset_for_word(w, category_syn) for w in words]

    min_sim = 1.0

    for i in range(len(synsets)):
        for j in range(i + 1, len(synsets)):
            sim = synsets[i].path_similarity(synsets[j]) or 0
            min_sim = min(min_sim, sim)

    return min_sim

def min_pairwise_similarity(words, model):
    vectors = [model[w] for w in words if w in model]

    min_sim = 1.0

    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            sim = cosine_sim(vectors[i], vectors[j])
            min_sim = min(min_sim, sim)

    return min_sim

def score(group):
    model = get_model()

    words = group["words"]
    category_syn = group["meta"]["synset"]

    # -----------------------
    # HARD FILTERS (reject early)
    # -----------------------

    if any(len(w) < 3 for w in words):
        return float("-inf")

    # Missing embeddings
    if any(w not in model for w in words):
        return float("-inf")

    # Must share structure
    if not share_hypernym(words, category_syn):
        return float("-inf")

    # Must be same semantic type
    if not same_lexname(words, category_syn):
        return float("-inf")
    
    if category_alignment(words, category_syn) < 0.75:
        return float("-inf")
    
    if any(zipf_frequency(w, "en") < 3.0 for w in words):
        return float("-inf")
    
    if min_wordnet_similarity(words, category_syn) < 0.15:
        return float("-inf")
    
    # if min_pairwise_similarity(words, model) < 0.15:
    #     return float("-inf")
    
    if pos_consistency(words) < 0.75:
        return float("-inf")

    # -----------------------
    # SOFT SCORING
    # -----------------------

    tightness = cluster_tightness(words, model)
    redundancy = redundancy_penalty(words, model, threshold=0.65)
    freq = avg_frequency(words)
    min_sim = min_similarity_to_centroid(words, model)
    pos_score = pos_consistency(words)
    gen_pen = generic_penalty(words)
    stem_pen = stem_penalty(words)

    return (
        3.5 * tightness +
        2.5 * min_sim +
        1.5 * pos_score + 
        1.5 * freq -
        3.0 * redundancy -
        2.0 * gen_pen -
        2.0 * stem_pen
    )

'''

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


def get_synsets(words, category_syn):
    synsets = []
    for w in words:
        candidates = wn.synsets(w, pos='n')
        if not candidates:
            return None

        best = max(
            candidates,
            key=lambda s: s.path_similarity(category_syn) or 0
        )
        synsets.append(best)

    return synsets


# -----------------------
# HARD FILTERS
# -----------------------

def is_valid_group(words, model, category_syn):
    # basic sanity
    if any(len(w) < 2 for w in words):
        return False

    if any(w not in model for w in words):
        return False

    if any(zipf_frequency(w, "en") < 3.0 for w in words):
        return False

    # resolve synsets once
    synsets = get_synsets(words, category_syn)
    if not synsets:
        return False

    # shared hypernym (core structural constraint)
    hypernym_sets = [set(s.hypernyms()) for s in synsets]
    if not set.intersection(*hypernym_sets):
        return False

    # loose alignment (less strict than before)
    aligned = category_alignment(words, category_syn, synsets)
    if aligned < 0.50:   # was 0.75 → loosened
        return False

    # embedding coherence floor
    # vectors = [model[w] for w in words]
    # for i in range(len(vectors)):
    #     for j in range(i + 1, len(vectors)):
    #         if cosine_sim(vectors[i], vectors[j]) < 0.30:
    #             return False
            
    if cluster_tightness(words, model) < 0.70:
        return False

    return True


# -----------------------
# LIGHT SCORING
# -----------------------

def cluster_tightness(words, model):
    vectors = [model[w] for w in words]
    centroid = np.mean(vectors, axis=0)
    return np.mean([cosine_sim(v, centroid) for v in vectors])

def category_alignment(words, category_syn, synsets):
    return sum(
        any(category_syn in path for path in s.hypernym_paths())
        for s in synsets
    ) / len(synsets)


def min_similarity(words, model):
    vectors = [model[w] for w in words]
    sims = [
        cosine_sim(vectors[i], vectors[j])
        for i in range(len(vectors))
        for j in range(i + 1, len(vectors))
    ]
    return min(sims)


def avg_frequency(words):
    return sum(zipf_frequency(w, "en") for w in words) / len(words)


def score(group):
    if group.get("meta", {}).get("type") == "anagram":
        return anagram_score(group)
    
    model = get_model()

    words = group["words"]
    category_syn = group["meta"]["synset"]

    # HARD FILTER
    if not is_valid_group(words, model, category_syn):
        return float("-inf")

    # SIMPLE SCORE (no heavy weighting)
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