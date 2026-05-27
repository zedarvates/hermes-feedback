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
/r *        →  1/5  (poor)
/r **       →  2/5  (needs work)
/r ***      →  3/5  (okay)
/r ****     →  4/5  (good)
/r *****    →  5/5  (excellent)

/r **** diagnosis   →  rate with context
/r **** 2           →  rate 2 turns ago
```

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

## Roadmap

- [x] `/r` star detection + ndjson storage
- [x] `/poll` structured surveys
- [x] Template-based suggestion prompts (zero LLM)
- [x] Implicit signals (/retry, /undo, keywords)
- [x] Anti-fatigue timer (15min)
- [x] ASCII dashboard
- [x] DPO dataset export
- [ ] Gateway inline buttons (Telegram/Discord via clarify #24191)
- [ ] `hermes feedback` native CLI subcommand
