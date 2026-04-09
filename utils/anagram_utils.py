from wordfreq import top_n_list, zipf_frequency

def load_words(n=50000):
    return top_n_list("en", n)

def is_valid_word(w):
    return w.isalpha() and len(w) >= 3

def sort_letters(w):
    return "".join(sorted(w))

def passes_frequency(words, min_zipf=3.5):
    return all(zipf_frequency(w, "en") >= min_zipf for w in words)

def too_trivial(words):
    # prevent obvious sets like act/cat/tac
    return all(len(w) <= 4 for w in words)