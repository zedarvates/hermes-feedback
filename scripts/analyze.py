#!/usr/bin/env python3
"""analyze.py — Analyze feedback trends from ratings.ndjson.

Usage:
  analyze.py                    full analysis
  analyze.py --summary          one-line summary
  analyze.py --export-dpo       export as DPO preference pairs
"""

import json, os, sys
from collections import Counter

FEED_DIR = os.path.expanduser("~/.hermes/feedback")
FILE = os.path.join(FEED_DIR, "ratings.ndjson")

def load():
    if not os.path.exists(FILE) or os.path.getsize(FILE) == 0:
        return []
    entries = []
    with open(FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries

def summary(entries):
    if not entries:
        return "No feedback yet."
    ratings = [e["rating"] for e in entries]
    avg = sum(ratings) / len(ratings)
    stars = {5: "★★★★★", 4: "★★★★☆", 3: "★★★☆☆", 2: "★★☆☆☆", 1: "★☆☆☆☆"}
    label = "Excellent" if avg >= 4.5 else "Good" if avg >= 3.5 else "Okay" if avg >= 2.5 else "Needs work"
    return f"{stars.get(round(avg), '?')} {avg:.2f}/5 — {label} ({len(entries)} ratings)"

def analyze(entries):
    if not entries:
        print("No feedback to analyze.")
        return
    total = len(entries)
    ratings = [e["rating"] for e in entries]
    avg = sum(ratings) / total
    counter = Counter(ratings)

    print(f"📊 Feedback Analysis — {total} ratings")
    print()
    print(f"Average: {avg:.2f}/5")
    print()
    for r in range(1, 6):
        c = counter.get(r, 0)
        bar = "█" * c
        print(f"  {r}★ {bar} ({c})")
    print()
    print("Recent ratings:")
    for e in entries[-5:]:
        print(f"  {e['timestamp'][:19]} | {e['rating']}★ | {e.get('context', '-')}")
    print()
    low = counter.get(1, 0) + counter.get(2, 0)
    high = counter.get(4, 0) + counter.get(5, 0)
    if low > high:
        print("⚠️ More low ratings than high — adjustment needed.")
    elif high > low * 3:
        print("👍 Positive trend — alignment is working.")
    else:
        print("→ Normal distribution, keep rating.")

def export_dpo(entries):
    """Export as simple DPO preference pairs.
    Each pair: high-rated response vs lower-rated response from similar context.
    """
    if len(entries) < 2:
        print("Need at least 2 ratings for DPO export.")
        return
    high = [e for e in entries if e["rating"] >= 4]
    low = [e for e in entries if e["rating"] <= 2]
    if not high or not low:
        print("Need both high (4-5★) and low (1-2★) ratings for pairs.")
        return
    pairs = []
    for h in high[:10]:
        for l in low[:10]:
            pairs.append({"chosen": h, "rejected": l})
    out = os.path.join(FEED_DIR, "dpo_pairs.json")
    with open(out, "w") as f:
        json.dump(pairs, f, indent=2)
    print(f"✓ {len(pairs)} DPO pairs exported to {out}")

if __name__ == "__main__":
    entries = load()
    if "--summary" in sys.argv:
        print(summary(entries))
    elif "--export-dpo" in sys.argv:
        export_dpo(entries)
    else:
        analyze(entries)
