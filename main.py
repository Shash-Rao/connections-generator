"""
main.py

Usage
-----
  python main.py                        # generate 300, print all
  python main.py --n 1000 --limit 20   # generate 1000, print first 20
  python main.py --n 100000 --save     # generate in batches, save to pool.db, no printing
  python main.py --stats               # print stats about pool.db
"""

import argparse
import json
import sqlite3
import time
from collections import Counter
from pathlib import Path

from scoring.embedding_scorer import score
from generators.synonym_generator import SynonymGenerator
from scoring.difficulty import assign_difficulties

DB_PATH = Path("pool.db")
BATCH_SIZE = 500  # how many to generate per batch when using --save


# ---------------------------------------------------------------------------
# SQLite helpers
# ---------------------------------------------------------------------------

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT,
            words       TEXT,
            score       REAL,
            difficulty  TEXT,
            type        TEXT,
            definition  TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def save_groups(conn, groups):
    rows = [
        (
            g["category"],
            json.dumps(g["words"]),
            g.get("score", 0.0),
            g.get("difficulty", ""),
            g["meta"]["type"],
            g["meta"]["definition"],
        )
        for g in groups
    ]
    conn.executemany(
        "INSERT INTO groups (category, words, score, difficulty, type, definition) "
        "VALUES (?,?,?,?,?,?)",
        rows,
    )
    conn.commit()


def db_total(conn):
    return conn.execute("SELECT COUNT(*) FROM groups").fetchone()[0]


def print_stats():
    if not DB_PATH.exists():
        print("No pool.db found. Run with --save first.")
        return
    with sqlite3.connect(DB_PATH) as conn:
        total = db_total(conn)
        by_type = conn.execute(
            "SELECT type, COUNT(*) FROM groups GROUP BY type"
        ).fetchall()
        by_diff = conn.execute(
            "SELECT difficulty, COUNT(*) FROM groups GROUP BY difficulty"
        ).fetchall()
    print(f"\n=== pool.db ===")
    print(f"Total groups: {total}")
    print("\nBy type:")
    for t, c in by_type:
        print(f"  {t}: {c}")
    print("\nBy difficulty:")
    for d, c in by_diff:
        print(f"  {d or 'unset'}: {c}")


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def score_and_filter(raw):
    kept = []
    for g in raw:
        s = score(g)
        if s != float("-inf"):
            g["score"] = s
            kept.append(g)
    return kept


def run_batch_save(target_n, combo_sample_limit):
    """
    Generate target_n groups in batches of BATCH_SIZE, saving each batch
    to pool.db. Prints a one-line progress update per batch instead of
    flooding the terminal.
    """
    gen = SynonymGenerator(
        enforce_global_dedup=False,
        combo_sample_limit=combo_sample_limit,
    )

    with sqlite3.connect(DB_PATH) as conn:
        init_db(conn)
        start_total = db_total(conn)

    saved = 0
    raw_total = 0
    t0 = time.time()

    print(f"Generating up to {target_n} groups in batches of {BATCH_SIZE}...")
    print(f"Saving to {DB_PATH}  (already contains {start_total} groups)\n")

    while saved < target_n:
        batch_target = min(BATCH_SIZE, target_n - saved)
        raw = gen.generate_n(n=batch_target)
        raw_total += len(raw)

        if not raw:
            print("WordNet exhausted — stopping early.")
            break

        kept = score_and_filter(raw)
        if kept:
            kept = assign_difficulties(kept)
            with sqlite3.connect(DB_PATH) as conn:
                save_groups(conn, kept)
                total_in_db = db_total(conn)

            saved += len(kept)
            elapsed = time.time() - t0
            yield_pct = 100 * saved / raw_total if raw_total else 0
            print(
                f"  batch done | kept {len(kept):>4} / {len(raw)} "
                f"| total saved this run: {saved:>6} "
                f"| db total: {total_in_db:>7} "
                f"| yield: {yield_pct:.0f}% "
                f"| {elapsed:.0f}s elapsed"
            )
        else:
            print(f"  batch produced 0 kept groups — continuing...")

    elapsed = time.time() - t0
    print(f"\nDone. Saved {saved} groups in {elapsed:.1f}s.")


def run_print(target_n, limit, combo_sample_limit):
    """Generate and print to terminal — for small runs only."""
    gen = SynonymGenerator(
        enforce_global_dedup=False,
        combo_sample_limit=combo_sample_limit,
    )

    t0 = time.time()
    raw = gen.generate_n(n=target_n)
    elapsed = time.time() - t0

    synonym_count = sum(1 for g in raw if g["meta"]["type"] == "synonym")
    cross_count = sum(1 for g in raw if g["meta"]["type"] == "cross_synset")
    print(f"\nGenerated {len(raw)} raw groups in {elapsed:.1f}s")
    print(f"  synonym:      {synonym_count}")
    print(f"  cross_synset: {cross_count}")

    kept = score_and_filter(raw)
    print(f"Kept {len(kept)} groups after scoring ({len(raw) - len(kept)} filtered).\n")

    if not kept:
        print("No groups passed scoring.")
        return

    kept = assign_difficulties(kept)

    display = kept[:limit] if limit else kept
    for i, g in enumerate(display, start=1):
        print(f"Group {i} [{g['meta']['type']}]: {g['category']}")
        print(f"  Difficulty: {g['difficulty']}")
        print(f"  Words:      {', '.join(g['words'])}")
        print()

    if limit and limit < len(kept):
        print(f"... {len(kept) - limit} more groups not shown (use --limit to see more)\n")

    diff_counts = Counter(g["difficulty"] for g in kept)
    print("Difficulty breakdown:")
    for d, c in sorted(diff_counts.items()):
        print(f"  {d}: {c}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=300,
                        help="Number of groups to generate (default: 300)")
    parser.add_argument("--save", action="store_true",
                        help="Save to pool.db in batches instead of printing")
    parser.add_argument("--stats", action="store_true",
                        help="Print pool.db stats and exit")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max groups to print (default: all)")
    parser.add_argument("--combo-limit", type=int, default=100,
                        help="Combinations sampled per synset (default: 100)")
    args = parser.parse_args()

    if args.stats:
        print_stats()
        return

    if args.save:
        run_batch_save(args.n, args.combo_limit)
    else:
        run_print(args.n, args.limit, args.combo_limit)


if __name__ == "__main__":
    main()