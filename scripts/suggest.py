#!/usr/bin/env python3
"""suggest.py — Print a pre-written feedback prompt (zero LLM tokens). 

Includes anti-fatigue timer: won't suggest more than once per 15 minutes.

Usage:
  suggest.py <pattern> [context]
  suggest.py session-end            → end-of-session recap
  suggest.py can-suggest            → check if cooldown has passed
  suggest.py --list                 → list available patterns

Patterns: task_complete, diagnosis, exploration, long_session, error_recovery
"""
import json, os, sys, time
from datetime import datetime, timezone

FEED_DIR = os.path.expanduser("~/.hermes/feedback")
PATTERNS_DIR = os.path.join(FEED_DIR, "patterns")
PROMPTS_DIR = os.path.join(PATTERNS_DIR, "prompts")
PATTERNS_FILE = os.path.join(PATTERNS_DIR, "patterns.json")
LAST_SUGGEST_FILE = os.path.join(FEED_DIR, "last_suggest.txt")

COOLDOWN_SECONDS = 15 * 60  # 15 minutes
COOLDOWN_TURNS = 10         # or 10 conversation turns

def get_prompt(pattern):
    paths = [
        os.path.join(PROMPTS_DIR, f"{pattern}.txt"),
    ]
    # Also check relative to script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rel = os.path.join(script_dir, "..", "patterns", "prompts", f"{pattern}.txt")
    paths.append(os.path.normpath(rel))

    for p in paths:
        p = os.path.normpath(p)
        if os.path.exists(p):
            with open(p) as f:
                return f.read().strip()
    return None

def load_patterns():
    paths = [PATTERNS_FILE, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "patterns", "patterns.json")]
    for p in paths:
        p = os.path.normpath(p)
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return {"patterns": []}

def can_suggest():
    """Check anti-fatigue: return (True, None) if enough time has passed, (False, msg) otherwise."""
    if not os.path.exists(LAST_SUGGEST_FILE):
        return True, None
    try:
        with open(LAST_SUGGEST_FILE) as f:
            last_ts = float(f.read().strip())
        elapsed = time.time() - last_ts
        remaining = COOLDOWN_SECONDS - elapsed
        if remaining > 0:
            mins = int(remaining / 60)
            return False, f"Cooldown: {mins}m remaining"
        return True, None
    except (ValueError, OSError):
        return True, None

def mark_suggested():
    """Record that a suggestion was made (anti-fatigue)."""
    with open(LAST_SUGGEST_FILE, "w") as f:
        f.write(str(time.time()))

def print_session_end():
    """End-of-session recap with stats if available."""
    prompt = get_prompt("session_end")
    if not prompt:
        return
    # Try to include basic stats
    ratings_file = os.path.join(FEED_DIR, "ratings.ndjson")
    count = 0
    if os.path.exists(ratings_file):
        count = sum(1 for _ in open(ratings_file))
    print(f"  Session ended ({count} ratings total).")
    print()
    print(prompt)

if __name__ == "__main__":
    if len(sys.argv) < 2 or "--list" in sys.argv:
        patterns = load_patterns()
        print("Available patterns:")
        for p in patterns.get("patterns", []):
            triggers = ", ".join(p.get("triggers", [])[:3])
            print(f"  {p['id']:20s} → {triggers}")
        sys.exit(0)

    pattern = sys.argv[1]
    context = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    if pattern == "can-suggest":
        ok, msg = can_suggest()
        if ok:
            print("yes")
        else:
            print(f"no:{msg}")
        sys.exit(0)

    if pattern == "session-end":
        print_session_end()
        sys.exit(0)

    # Anti-fatigue check
    ok, msg = can_suggest()
    if not ok:
        # Silent: don't print anything if in cooldown
        sys.exit(0)

    prompt = get_prompt(pattern)
    if prompt is None:
        print(f"✗ Unknown pattern '{pattern}'. Run 'suggest.py --list' to see available patterns.")
        sys.exit(1)

    # Mark as suggested (anti-fatigue)
    mark_suggested()
    print(prompt)
