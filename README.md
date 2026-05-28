# Hermes Feedback — `/r ★...★` Preference Rating System

A lightweight, **token-optimized** feedback system for [Hermes Agent](https://hermes-agent.nousresearch.com).  
Star ratings, polls, implicit signals, and DPO export — with **zero LLM token cost** for most operations.

## Features

| Feature | Cost | How |
|---------|------|-----|
| `/r ★★★★` quick rating | **0 tokens** | `rate.py` writes to ndjson |
| `/poll` structured survey | **0 tokens** | `poll.py` prints multi-topic template |
| Auto-suggest after tasks | **~15 tokens** | `suggest.py` reads pre-written `.txt` file |
| Implicit signals (retry, undo, keywords) | **0 tokens** | `implicit.py` maps action → rating |
| ASCII dashboard | **0 tokens** | `dashboard.py` reads ndjson, prints charts |
| DPO dataset export | **0 tokens** | `analyze.py --export-dpo` |
| Weekly trend analysis | **~200 tokens** | cron agent summarizes |

Total per feedback cycle: **~15 tokens** (the tool call). Everything else is filesystem.

## Quick start

```bash
# Install
cp scripts/*.py ~/.hermes/scripts/
cp -r patterns/ ~/.hermes/feedback/patterns/
cp -r skill/ ~/.hermes/skills/hermes/feedback-rate/
chmod +x ~/.hermes/scripts/*.py

# Weekly analysis
hermes cron add --name feedback-analyze \
  --schedule "0 8 * * 1" \
  --script analyze.py \
  --prompt "Analyze feedback trends and surface insights"
```

## Usage

### Quick rating

```
rate *        →  1/5  (poor)
rate **       →  2/5  (needs work)
rate ***      →  3/5  (okay)
rate ****     →  4/5  (good)
rate *****    →  5/5  (excellent)

rate **** diagnosis       →  rate with context
rate **** 2               →  rate 2 turns ago
```

### Poll — structured survey

```
/poll Network diagnosis, Code clarity, Suggestions relevance
```

Each topic gets its own rating line.

### Dashboard

```bash
python3 ~/.hermes/scripts/dashboard.py              # ASCII art terminal
python3 ~/.hermes/scripts/dashboard.py --summary    # one-liner
python3 ~/.hermes/scripts/dashboard.py --html       # open in browser
```

### Analyze & export

```bash
python3 ~/.hermes/scripts/analyze.py                # full report
python3 ~/.hermes/scripts/analyze.py --export-dpo   # DPO pairs
```

## Token optimization — the "patterns" system

Instead of generating suggestion text with the LLM (expensive), the agent calls `suggest.py <pattern>` which reads a **pre-written template** from disk:

```bash
python3 ~/.hermes/scripts/suggest.py task_complete     # after finishing work
python3 ~/.hermes/scripts/suggest.py diagnosis          # after debugging
python3 ~/.hermes/scripts/suggest.py exploration        # after ideas session
python3 ~/.hermes/scripts/suggest.py long_session       # 25+ turns
python3 ~/.hermes/scripts/suggest.py error_recovery     # after fixing a mistake
python3 ~/.hermes/scripts/suggest.py session_end        # on /quit or /new
python3 ~/.hermes/scripts/suggest.py can-suggest        # anti-fatigue check
```

Templates are in `patterns/prompts/*.txt`. Every read is instantaneous and costs nothing.

## Anti-fatigue

The system never suggests a rating more than **once per 15 minutes** (or 10 conversation turns). The cooldown is stored in `~/.hermes/feedback/last_suggest.txt`.

## Implicit signals

These generate automatic ratings without asking:

| Signal | Rating | Source |
|--------|--------|--------|
| `/retry` | 1★ | User rejected the response |
| `/undo` | 1★ | User undid the exchange |
| "parfait", "perfect", "excellent" | 5★ | Keyword match |
| "nul", "wrong", "stupid" | 1★ | Keyword match |

```bash
python3 ~/.hermes/scripts/implicit.py retry
python3 ~/.hermes/scripts/implicit.py keyword "parfait"
```

## Architecture

```
~/.hermes/feedback/
├── patterns/
│   ├── patterns.json              ← pattern definitions
│   └── prompts/*.txt              ← pre-written templates
├── ratings.ndjson                 ← all /r ratings (append-only)
├── polls.ndjson                   ← poll metadata
├── implicit_signals.ndjson        ← auto-detected signals
├── last_suggest.txt               ← anti-fatigue cooldown
├── dpo_pairs.json                 ← exported DPO training pairs
├── dashboard.html                 ← browser dashboard
└── stats.json                     ← cached analysis

~/.hermes/scripts/
├── rate.py                        ← save a rating
├── analyze.py                     ← trends + DPO export
├── suggest.py                     ← read pre-written template
├── poll.py                        ← structured survey
├── implicit.py                    ← auto-detect signals
└── dashboard.py                   ← ASCII + HTML dashboard
```

## Platform support

| Platform | `/r` text | `/poll` | Inline buttons |
|----------|-----------|---------|----------------|
| CLI/TUI  | ✅        | ✅      | —              |
| Telegram | ✅        | ✅ text | Planned (see clarify #24191) |
| Discord  | ✅        | ✅ text | Planned |
| Other    | ✅        | ✅ text | —              |

## Roadmap

- [x] `/r` star detection + ndjson storage
- [x] `/poll` structured surveys
- [x] Template-based suggestion prompts (zero LLM)
- [x] Implicit signals (/retry, /undo, keywords)
- [x] Anti-fatigue timer (15min)
- [x] ASCII + HTML dashboard
- [x] DPO dataset export
- [ ] Gateway inline buttons (Telegram/Discord)
- [ ] `hermes feedback` native CLI subcommand

## Inspiration

- [DPO (Rafailov et al., 2023)](https://arxiv.org/abs/2305.18290)
- [Context-CoT (Jin et al., 2026)](https://arxiv.org/abs/2305.18290)
- [Mechanical Sympathy](https://youtu.be/7M4XFi0aBDA)
- Hermes Agent [#24191](https://github.com/NousResearch/hermes-agent/issues/24191)

---

*by zedarvates — built from daily use of Hermes Agent*
