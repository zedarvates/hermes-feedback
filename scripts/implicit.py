#!/usr/bin/env python3
"""implicit.py — Detect implicit feedback signals from user actions.

Zero LLM tokens. Maps user actions to automatic star ratings.

Signals:
  /retry           → 1★ (user rejected the response)
  /undo            → 1★ (user undid the exchange)
  /exit, /quit     → triggers end-of-session summary
  "parfait" / "perfect" / "excellent"   → 5★ implicit
  "nul" / "faux" / "wrong" / "stupid"   → 1★ implicit

Usage:
  implicit.py <signal> [context]
  implicit.py check-retry      → outputs 1★ rating
  implicit.py check-undo       → outputs 1★ rating
  implicit.py keyword "parfait" → outputs 5★ if positive keyword
  implicit.py keyword "nul"    → outputs 1★ if negative keyword
"""

import json, os, sys
from datetime import datetime, timezone

FEED_DIR = os.path.expanduser("~/.hermes/feedback")
FILE = os.path.join(FEED_DIR, "implicit_signals.ndjson")
os.makedirs(FEED_DIR, exist_ok=True)

POSITIVE_KEYWORDS = [
    "parfait", "parfaite", "excellent", "excellente",
    "perfect", "great", "awesome", "amazing",
    "super", "bravo", "merci", "thanks",
    "good job", "bien joué", "bien joue",
]

NEGATIVE_KEYWORDS = [
    "nul", "nulle", "faux", "fausse",
    "wrong", "stupid", "terrible", "awful",
    "pas bien", "mauvais", "incorrect",
]

# User action → rating mapping (non-keyword signals)
ACTION_RATINGS = {
    "retry": 1,
    "undo": 1,
    "session-end": None,  # special: trigger recap
}

def save_implicit(signal, rating, context=""):
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "signal": signal,
        "rating": rating,
        "session": os.environ.get("HERMES_SESSION_ID", "unknown"),
        "context": context,
    }
    with open(FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return rating

def check_keyword(text):
    text_lower = text.lower().strip()
    for kw in POSITIVE_KEYWORDS:
        if kw in text_lower:
            return 5, f"positive keyword: {kw}"
    for kw in NEGATIVE_KEYWORDS:
        if kw in text_lower:
            return 1, f"negative keyword: {kw}"
    return None, None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: implicit.py <signal> [context]")
        print("Signals: retry, undo, session-end, keyword <text>")
        sys.exit(1)

    signal = sys.argv[1]
    context = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    if signal == "keyword" and context:
        rating, desc = check_keyword(context)
        if rating:
            save_implicit(signal, rating, desc)
            print(f"✓ Implicit {rating}★ — {desc}")
        else:
            print("→ No implicit signal detected")
    elif signal in ACTION_RATINGS:
        rating = ACTION_RATINGS[signal]
        if rating is not None:
            save_implicit(signal, rating, context)
            print(f"✓ Implicit {rating}★ — signal: {signal}")
        else:
            print(f"→ Signal '{signal}' triggers end-of-session recap")
    else:
        print(f"✗ Unknown signal '{signal}'")
        sys.exit(1)
