#!/usr/bin/env python3
"""Comprehensive tests for generators/purple.py

Run this script from the project root. It will perform smoke tests and strategy-specific
validations when the necessary NLTK corpora are available. Tests are permissive: strategies
may return None if no valid group is found; that is treated as a non-failure.
"""
import sys
import traceback

from collections import defaultdict

import nltk
# nltk.download('cmudict')
# nltk.download('wordnet')
# nltk.download('omw-1.4')
# print(nltk.data.path)

from generators import PurpleGenerator


def has_nltk_corpora(names):
    for n in names:
        try:
            nltk.data.find(f'corpora/{n}')
        except LookupError:
            return False
    return True


def fail(msg, exc=None):
    print('FAILED:', msg)
    if exc:
        traceback.print_exception(type(exc), exc, exc.__traceback__)
    sys.exit(2)


def main():
    g = PurpleGenerator()

    # Basic smoke test: generate a few times; returned value must be None or a dict with 4 words
    try:
        for i in range(5):
            out = g.generate()
            assert out is None or (
                isinstance(out, dict)
                and 'words' in out
                and isinstance(out['words'], list)
                and len(out['words']) == 4
            )
        print('SMOKE: generate() OK')
    except AssertionError as e:
        fail('generate() returned invalid structure', e)

    # Homophone strategy test (requires cmudict)
    if has_nltk_corpora(['cmudict']):
        try:
            cmu = nltk.corpus.cmudict.dict()
            pron_map = defaultdict(set)
            for w, prons in cmu.items():
                for p in prons:
                    pron_map[tuple(p)].add(w)

            res = g._homophone_group()
            if res is None:
                print('HOMOPHONE: no group found (allowed)')
            else:
                print("Entered else (res is not None)")
                words = res.get('words')
                assert isinstance(words, list) and len(words) == 4
                print("Words:", words)
                for w in words:
                    wl = w.lower()
                    assert wl in cmu, f"{w} not in cmudict"
                    # verify at least one pronunciation has other words
                    has_hom = False
                    for p in cmu[wl]:
                        if len(pron_map[tuple(p)] - {wl}) > 0:
                            has_hom = True
                            break
                    assert has_hom, f"{w} has no homophone in cmudict"
                print('HOMOPHONE: strategy OK')
        except AssertionError as e:
            fail('homophone strategy failed checks', e)
    else:
        print('HOMOPHONE: skipped (cmudict not installed)')

    # Shortened-synonym strategy (requires wordnet)
    if has_nltk_corpora(['wordnet']):
        try:
            from nltk.corpus import wordnet as wn

            res = g._shortened_synonym_group()
            if res is None:
                print('SHORTENED-SYNONYM: no group found (allowed)')
            else:
                words = res.get('words')
                assert isinstance(words, list) and len(words) == 4
                key_syn = res.get('meta', {}).get('short_synset')
                assert key_syn is not None
                print("words:", words)
                for w in words:
                    short = w[:-1]
                    syns = wn.synsets(short)
                    assert syns, f'shortened form {short} has no synsets'
                    # require the representative synset to appear among the shortened form synsets
                    assert any(key_syn == s for s in syns), (
                        f'shortened form {short} does not map to chosen synset {key_syn}'
                    )
                print('SHORTENED-SYNONYM: strategy OK')
        except AssertionError as e:
            fail('shortened-synonym strategy failed checks', e)
    else:
        print('SHORTENED-SYNONYM: skipped (wordnet not installed)')

    # Common-followed-by strategy (requires wordnet)
    if has_nltk_corpora(['wordnet']):
        try:
            from nltk.corpus import wordnet as wn

            res = g._common_followed_by_group()
            if res is None:
                print('FOLLOWED-BY: no group found (allowed)')
            else:
                tail = res.get('meta', {}).get('tail')
                words = res.get('words')
                assert tail and isinstance(words, list) and len(words) == 4
                for head in words:
                    compound = f"{head}_{tail}"
                    syns = wn.synsets(compound)
                    assert syns, f'compound {compound} not found in WordNet'
                print('FOLLOWED-BY: strategy OK')
        except AssertionError as e:
            fail('followed-by strategy failed checks', e)
    else:
        print('FOLLOWED-BY: skipped (wordnet not installed)')

    print('\nALL TESTS COMPLETED')


if __name__ == '__main__':
    main()
