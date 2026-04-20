import csv
import os
import random
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils.filters import is_common_word

DATASET_PATH = os.path.join(ROOT_DIR, 'datasets', 'LADECv1-2019.csv')


def get_dict():
    second_to_first = {}
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stim = row['stim'].strip()
            c1 = row['c1'].strip()
            c2 = row['c2'].strip()
            if is_common_word(stim, min_freq=2.5):
                second_to_first.setdefault(c2, []).append(c1)

    return {k: v for k, v in second_to_first.items() if len(v) >= 4}


def sample_compounds():
    second_to_first = get_dict()
    if not second_to_first:
        return []
    

    c2 = random.choice(list(second_to_first.keys()))
    c1_list = second_to_first[c2]
    sampled_c1 = random.sample(c1_list, 4)
    return sampled_c1, c2


def generate():
    words, second_part = sample_compounds()
    if not words:
        return None
    return {
        "category_name": f"___{second_part}",
        "words": words,
        "category_type": "fill_blank",
        "difficulty": "purple",
    }


if __name__ == '__main__':
    print(generate())