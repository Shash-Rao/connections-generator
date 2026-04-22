import random
from collections import defaultdict

import nltk
from nltk.corpus import cmudict

from utils.filters import is_clean_word, is_common_word, is_proper_noun



def generate():
    """Find 4 words where each word has at least one homophone (not necessarily the same)."""
    try:
        cmu = cmudict.dict()
    except Exception:
        return None

    # Build pronunciation -> words map
    pron_map = defaultdict(set)
    for w, prons in cmu.items():
        if not is_clean_word(w) or not is_common_word(w):
            continue
        for p in prons:
            pron_map[tuple(p)].add(w)

    # Collect eligible words that have at least one homophone
    eligible = []  # (word, rep_pron)
    for w, prons in cmu.items():
        if not is_clean_word(w) or not is_common_word(w):
            continue
        homs = set()
        for p in prons:
            homs |= (pron_map[tuple(p)] - {w})
        if homs:
            rep = tuple(prons[0])
            eligible.append((w, rep))

    # Group by representative pronunciation and pick four distinct pronunciation groups
    rep_to_words = defaultdict(list)
    ct = 0
    for w, rep in eligible:
        if not is_proper_noun(w) and is_common_word(w):
            rep_to_words[rep].append(w)
        elif is_proper_noun(w):
            print(w)
            ct += 1
            if ct == 10:
                break
    print("rep_to_words keys (representative pronunciations):", list(rep_to_words.keys()))
    ct = 0
    for k, v in rep_to_words.items():
        print(k)
        print(v)
        ct += 1
        if ct == 5:
            break

    reps = list(rep_to_words.keys())
    if len(reps) < 4:
        print("Not enough distinct representative pronunciations with homophones found.")
        return None

    print("Total representative pronunciations with homophones:", len(reps))
    chosen_reps = set([r for r in reps if len(rep_to_words[r]) >= 2])
    print("Chosen representative pronunciations:", chosen_reps)
    for r in chosen_reps:
        print(f"Words for pronunciation {r}:", rep_to_words[r])
    # chosen_reps = random.sample(reps, 4)
    print("Representative pronunciations chosen:", chosen_reps)
    for r in chosen_reps:
        print(f"Words for pronunciation {r}:", rep_to_words[r])
    words = [random.choice(rep_to_words[r]) for r in chosen_reps]

    return {
        "category": "Words where each has at least one homophone",
        "words": words,
        "meta": {"strategy": "homophone", "reps": chosen_reps},
    }
