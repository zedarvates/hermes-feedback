#!/usr/bin/env python3
"""rate.py — Save a star rating to the feedback log.

Usage:
  rate.py <1-5> [context]

Examples:
  rate.py 5 "Great diagnosis of the network issue"
  rate.py 2 "Response was too vague"
"""

import json, os, sys
from datetime import datetime, timezone

FEED_DIR = os.path.expanduser("~/.hermes/feedback")
FILE = os.path.join(FEED_DIR, "ratings.ndjson")
os.makedirs(FEED_DIR, exist_ok=True)

if len(sys.argv) < 2:
    print("Usage: rate.py <1-5> [context]")
    sys.exit(1)

try:
    rating = int(sys.argv[1])
except ValueError:
    print("Error: rating must be a number 1-5")
    sys.exit(1)

if rating < 1 or rating > 5:
    print("Error: rating must be between 1 and 5")
    sys.exit(1)

context = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

entry = {
    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "rating": rating,
    "session": os.environ.get("HERMES_SESSION_ID", "unknown"),
    "topic": os.environ.get("HERMES_TOPIC", ""),
    "context": context,
}

with open(FILE, "a") as f:
    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

count = sum(1 for _ in open(FILE))
print(f"✓ Rating {rating}/5 saved ({count} total)")
