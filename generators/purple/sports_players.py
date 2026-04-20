import csv
import os
import random
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils.filters import is_common_word

NBA_DATASET = os.path.join(ROOT_DIR, 'datasets', 'nba_teams.csv')
NFL_DATASET = os.path.join(ROOT_DIR, 'datasets', 'nfl_teams.csv')
MLB_DATASET = os.path.join(ROOT_DIR, 'datasets', 'mlb_teams.csv')
datasets = {"nba": NBA_DATASET, "nfl": NFL_DATASET, "mlb": MLB_DATASET}


def get_dict():
    league_to_teams = {}
    nba_teams = []
    for league, dataset in datasets.items():
        with open(dataset, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            col_name = 'Team' if 'Team' in reader.fieldnames else 'Name'
            teams = []
            for row in reader:
                name = row[col_name].strip().split(" ")[-1]
                if name[-1] == 's':
                    single = name[:-1].lower()
                    if is_common_word(single):
                        teams.append(name[:-1].lower())  # Remove trailing 's' for plural teams
        league_to_teams[league] = teams
    return league_to_teams


def sample_compounds():
    league_to_teams = get_dict()
    if not league_to_teams:
        return []

    league = random.choice(list(league_to_teams.keys()))
    teams = league_to_teams[league]
    sampled_teams = random.sample(teams, 4)
    return sampled_teams, f"{league.upper()} players"


def generate():
    teams, category = sample_compounds()
    if not teams:
        return None
    return {
        "category_name": category,
        "words": teams,
        "category_type": "sports_players",
        "difficulty": "purple",
    }


if __name__ == '__main__':
    print(generate())