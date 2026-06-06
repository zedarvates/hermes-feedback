---
name: feedback-rate
description: "Handle /r ★...★ feedback ratings, /poll surveys, implicit signals, and end-of-session prompts. Token-optimized — zero LLM for suggestions."
version: 2.0.0
author: Hermes Agent
platforms: [linux, macos]
---

# Feedback Rate — `/r` & `/poll` Handler

## Quick rating

```
hermes-feedback rate 4     →  4/5  (good)
hermes-feedback rate 5 "Great diagnosis"
hermes-feedback poll Network, Code clarity, Suggestions
```

> **Note:** All operations available via the unified `hermes-feedback` CLI.
> The JSONL file is still called `/r`-themed (`ratings.ndjson`) for DPO culture compatibility.

## Poll — structured multi-topic survey

```
/poll Network, Code clarity, Suggestions
```

Each topic gets its own rating line. File saved to `~/.hermes/feedback/polls.ndjson`.

## Token cost

| Action | LLM tokens | Mechanism |
|--------|-----------|-----------|
| Save `/r ★★★★` | 0 | `python3 rate.py` writes to ndjson |
| Suggest rating | ~15 | `suggest.py` reads pre-written `.txt` file |
| Weekly analysis | ~200 | cron agent summarizes |
| Implicit signal | 0 | `implicit.py` maps action → rating (no LLM) |
| Dashboard | 0 | `dashboard.py` reads ndjson, prints charts |
| DPO export | 0 | `analyze.py --export-dpo` |

## Suggestion patterns (zero LLM)

Call `suggest.py <pattern>` which reads from disk, not from an LLM:

```bash
python3 ~/.hermes/scripts/suggest.py task_complete    # after finishing work
python3 ~/.hermes/scripts/suggest.py diagnosis         # after debugging
python3 ~/.hermes/scripts/suggest.py exploration       # after ideas session
python3 ~/.hermes/scripts/suggest.py long_session      # 25+ turns
python3 ~/.hermes/scripts/suggest.py error_recovery    # after fixing a mistake
python3 ~/.hermes/scripts/suggest.py session_end       # on /quit or /new
python3 ~/.hermes/scripts/suggest.py can-suggest       # anti-fatigue check
```

## Anti-fatigue

- Max **1 suggestion per 15 minutes**
- Checked via `suggest.py can-suggest` before printing any prompt
- Timer stored in `~/.hermes/feedback/last_suggest.txt`

## Implicit signals (zero interaction)

These actions generate automatic ratings without asking:

| Signal | Rating | Source |
|--------|--------|--------|
| `/retry` | 1★ | User rejected the response |
| `/undo` | 1★ | User undid the exchange |
| "parfait", "perfect", "excellent" | 5★ | NLP keyword match |
| "nul", "wrong", "stupid" | 1★ | NLP keyword match |

```bash
python3 ~/.hermes/scripts/implicit.py keyword "parfait"
python3 ~/.hermes/scripts/implicit.py retry
```

## Dashboard

```bash
python3 ~/.hermes/scripts/dashboard.py             # ASCII art in terminal
python3 ~/.hermes/scripts/dashboard.py --summary   # one-liner
python3 ~/.hermes/scripts/dashboard.py --html      # HTML file in ~/.hermes/feedback/
```

## Analyze & export

```bash
python3 ~/.hermes/scripts/analyze.py                # full report
python3 ~/.hermes/scripts/analyze.py --export-dpo   # DPO pairs
```

## Installation

```bash
cp scripts/*.py ~/.hermes/scripts/
cp -r patterns/ ~/.hermes/feedback/patterns/
cp -r skill/ ~/.hermes/skills/hermes/feedback-rate/

# Weekly analysis cron
hermes cron add --name feedback-analyze \
  --schedule "0 8 * * 1" \
  --script analyze.py \
  --prompt "Analyze feedback trends and surface insights"
```

## Gateway integration (inline buttons)

The `references/gateway-integration.md` and `scripts/feedback_gateway.py` files
contain the full implementation for Telegram/Discord star rating buttons:

```
┌─────────────────────────────────────┐
│  ❓ How was this response?           │
│                                     │
│  [⭐] [⭐⭐] [⭐⭐⭐] [⭐⭐⭐⭐] [⭐⭐⭐⭐⭐]  │
└─────────────────────────────────────┘
```

On click → rating saved to `~/.hermes/feedback/ratings.ndjson`, message edits
to "📊 ⭐⭐⭐ 3/5 — thanks!". Zero LLM tokens for the entire interaction.

### Block-and-wait primitive (same shape as clarify #24191)

```python
from scripts.feedback_gateway import register_gateway_feedback, wait_for_feedback
fb_id = "fb_..."  # unique ID
entry = register_gateway_feedback(fb_id)
result = wait_for_feedback(fb_id, timeout=600)  # blocks; returns 1-5 or None
```

### Telegram blueprint (in `feedback_gateway.py blueprint`)

Add to `gateway/platforms/telegram.py`:
1. `send_feedback_buttons()` method on `TelegramAdapter` — renders 5 stars
2. `fb:` handler in `_handle_callback_query()` — resolves rating via `resolve_gateway_feedback()`
3. `_feedback_state` dict in `__init__`

### CLI test

```bash
python3 ~/.hermes/scripts/feedback_gateway.py save 5 "test"
python3 ~/.hermes/scripts/feedback_gateway.py blueprint
```

## Roadmap

- [x] `/r` star detection + ndjson storage
- [x] `/poll` structured surveys
- [x] Template-based suggestion prompts (zero LLM)
- [x] Implicit signals (/retry, /undo, keywords)
- [x] Anti-fatigue timer (15min)
- [x] ASCII dashboard
- [x] DPO dataset export
- [x] Gateway inline buttons — code & blueprint done (needs tg.py integration)
- [ ] `hermes feedback` native CLI subcommand
