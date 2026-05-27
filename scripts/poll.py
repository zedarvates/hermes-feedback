#!/usr/bin/env python3
"""poll.py — Start a structured poll based on the current discussion topics.

Zero LLM tokens: reads from pre-written templates, just interpolates
the topic names.

Usage:
  poll.py "topic1" "topic2" "topic3"
  poll.py "Network diagnosis" "Code clarity" "Suggestions relevance"
"""

import json, os, sys
from datetime import datetime, timezone

FEED_DIR = os.path.expanduser("~/.hermes/feedback")
os.makedirs(FEED_DIR, exist_ok=True)

if len(sys.argv) < 2:
    print("Usage: poll.py <topic1> [topic2] ...")
    print("Each topic gets its own star rating line.")
    sys.exit(1)

topics = sys.argv[1:]

print("📊 Quick poll — rate each aspect:")
print()
for i, topic in enumerate(topics, 1):
    print(f"  {i}. {topic}")
print()
print("Reply with:")
for i, topic in enumerate(topics, 1):
    print(f"  /r ★★★★ {i}   → rate '{topic}'")
print()
print("Or rate everything at once:")
print(f"  /r ★★★★     → global rating")

# Save the poll context so the agent can match responses
poll_id = datetime.now().strftime("%Y%m%d%H%M%S")
entry = {
    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "type": "poll",
    "poll_id": poll_id,
    "topics": topics,
    "context": " | ".join(topics),
}
polls_file = os.path.join(FEED_DIR, "polls.ndjson")
with open(polls_file, "a") as f:
    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

print(f"\nPoll ID: {poll_id}")
