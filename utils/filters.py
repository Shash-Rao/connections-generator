from wordfreq import zipf_frequency

MIN_WORD_FREQ = 3.5

BAD_CATEGORIES = {
    "entity", "object", "thing", "whole", "artifact"
}


def is_clean_word(word):
    return word.isalpha() and "_" not in word and "-" not in word


def is_common_word(word):
    return zipf_frequency(word, "en") >= MIN_WORD_FREQ


def is_good_category(syn):
    name = syn.lemmas()[0].name()

    if name in BAD_CATEGORIES:
        return False

    if syn.min_depth() < 7:
        return False

    return True


def get_valid_words_from_synset(syn):
    words = set()

    for lemma in syn.lemmas():
        w = lemma.name().lower()
        if is_clean_word(w) and is_common_word(w):
            words.add(w)

    return list(words)