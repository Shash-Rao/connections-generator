from wordfreq import zipf_frequency
from nltk.corpus import wordnet as wn

MIN_WORD_FREQ = 3.5

BAD_CATEGORIES = {
    "entity", "object", "thing", "whole", "artifact"
}


def is_clean_word(word):
    return word.isalpha() and "_" not in word and "-" not in word


def is_common_word(word, min_freq=MIN_WORD_FREQ):
    return zipf_frequency(word, "en") >= min_freq


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


def is_proper_noun(word):
    """Heuristic check whether `word` is a proper noun.

    Uses WordNet synsets but is conservative to avoid classifying generic
    nouns (e.g. 'adviser') as proper nouns. A synset must be in a
    person/location/group/organization lexname and the synset must contain
    lemma evidence of a proper name (capitalized lemma or multiword lemma).
    """
    if not isinstance(word, str) or not word:
        return False

    try:
        syns = wn.synsets(word, pos='n')
    except Exception:
        return False

    if not syns:
        return False

    proper_lexnames = {'noun.person', 'noun.location', 'noun.group', 'noun.organization'}

    for s in syns:
        if s.lexname() not in proper_lexnames:
            continue

        for lemma in s.lemmas():
            name = lemma.name()
            # Capitalization in the lemma (e.g., 'Paris' or 'New_York') is strong evidence
            if any(ch.isupper() for ch in name):
                return True

            # Multiword lemmas use underscores and often indicate named entities
            if '_' in name:
                parts = name.split('_')
                if all(part.isalpha() for part in parts):
                    return True

    return False