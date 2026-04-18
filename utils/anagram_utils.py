from wordfreq import top_n_list, zipf_frequency
from nltk.corpus import wordnet as wn


def load_words(n=200000, min_zipf_wordnet=2.5, debug=True):
    """
    Build a combined vocabulary from:
    - wordfreq top-N common English words
    - WordNet lemmas that are at least somewhat common

    Returns a sorted list of unique words.
    """
    wf_words = set(top_n_list("en", n))

    wn_words = set()
    for syn in wn.all_synsets():
        for lemma in syn.lemmas():
            w = lemma.name().lower()

            if not w.isalpha():
                continue

            # Keep only WordNet words with at least modest real-world usage
            if zipf_frequency(w, "en") < min_zipf_wordnet:
                continue

            wn_words.add(w)

    all_words = wf_words | wn_words

    if debug:
        print(f"wordfreq words: {len(wf_words)}")
        print(f"WordNet words kept: {len(wn_words)}")
        print(f"Combined unique words: {len(all_words)}")

    return sorted(all_words)


def is_valid_word(w, min_len=5, max_len=8):
    """
    Restrict to puzzle-friendlier word lengths.
    """
    return w.isalpha() and min_len <= len(w) <= max_len


def sort_letters(w):
    return "".join(sorted(w))


def passes_frequency(words, min_zipf=3.0):
    return all(zipf_frequency(w, "en") >= min_zipf for w in words)


def too_trivial(words):
    """
    Reject buckets that are too short/simple overall.
    You can make this stricter later.
    """
    return all(len(w) <= 4 for w in words)