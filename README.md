# Hermes Feedback 📊

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Status](https://img.shields.io/badge/status-active-brightgreen.svg)]()

**Token-optimized feedback system for Hermes Agent** — star ratings, polls, implicit signals, DPO export, and a unified CLI. Zero LLM tokens for the feedback loop itself.

## Features

- **Zero-LLM feedback** — implicit signals (retry, undo, keyword matching) cost 0 tokens
- **Star ratings** — `/r ★★★★` or `hermes-feedback rate 4 "context"` 
- **Polls** — structured multi-topic surveys with `/poll` or CLI
- **Suggestion patterns** — template-based prompts after task completion, diagnosis, long sessions (zero LLM)
- **Anti-fatigue** — max 1 suggestion per 15 minutes
- **Implicit signals** — auto-detect positive/negative sentiment from keywords, retry, undo
- **ASCII dashboard** — terminal-friendly trend overview
- **HTML dashboard** — exportable web view
- **DPO export** — generate preference pairs for fine-tuning
- **Gateway inline buttons** — Telegram/Discord star rating buttons (blueprint included)
- **Unified CLI** — `hermes-feedback` single entry point for all operations

## Quick Start

```bash
# Install
cp scripts/*.py ~/.hermes/scripts/
cp -r patterns/ ~/.hermes/feedback/patterns/
cp -r skill/ ~/.hermes/skills/hermes/feedback-rate/

# Rate a response
hermes-feedback rate 4 "Clear explanation of the network issue"

# Suggest feedback prompt (zero LLM)
hermes-feedback suggest task_complete

# View dashboard
hermes-feedback dashboard

# Weekly analysis cron
hermes cron add --name feedback-analyze \
  --schedule "0 8 * * 1" \
  --prompt "Analyze feedback trends and surface insights"
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `hermes-feedback rate <1-5> [context]` | Save a star rating |
| `hermes-feedback poll <topic1, topic2, ...>` | Multi-topic survey |
| `hermes-feedback implicit <signal> [context]` | Record implicit signal (retry, undo, keyword) |
| `hermes-feedback suggest <pattern>` | Generate suggestion prompt (zero LLM) |
| `hermes-feedback dashboard [--summary\|--html]` | View feedback trends |
| `hermes-feedback analyze [--export-dpo]` | Full analysis or DPO export |
| `hermes-feedback gateway <save\|blueprint>` | Gateway button tools |

### Signal types for `implicit`:

| Signal | Rating | Source |
|--------|--------|--------|
| `retry` | 1★ | User rejected the response |
| `undo` | 1★ | User undid the exchange |
| `session-end` | — | Triggers recap (no rating) |
| `keyword <text>` | 1★ or 5★ | Automatic sentiment detection |

### Suggestion patterns:

| Pattern | When |
|---------|------|
| `task_complete` | After 3+ tool calls producing a deliverable |
| `diagnosis` | After collaborative debugging |
| `exploration` | After R&D / creative session |
| `long_session` | 25+ turns or 3+ topics |
| `error_recovery` | After recovering from an agent error |
| `session_end` | On `/quit` or `/new` |

## Token Cost

| Action | LLM tokens | Mechanism |
|--------|-----------|-----------|
| Save `/r ★★★★` | 0 | Direct ndjson write |
| Suggest rating | ~15 | Reads pre-written template file |
| Weekly analysis | ~200 | Cron agent summarizes |
| Implicit signal | 0 | Keyword/action mapping |
| Dashboard | 0 | Reads ndjson, prints charts |
| DPO export | 0 | Generates pairs from existing ratings |
| Gateway button click | 0 | Callback → ndjson write |

## Workflow Patterns

### Generate and Filter
Over-generate suggestions → filter by implicit user feedback:
```
Agent → Generates N suggestions → Implicit feedback → Top-K kept
```

### Adversarial Verification
A second agent verifies feedback quality:
```
Agent A → Proposes improvement → Agent B → Verifies → Accept/Reject
```

## Gateway Integration (Telegram/Discord)

The `feedback_gateway.py` script contains a complete blueprint for inline star-rating buttons on Telegram and Discord:

```
┌─────────────────────────────────────┐
│  ❓ How was this response?           │
│                                     │
│  [⭐] [⭐⭐] [⭐⭐⭐] [⭐⭐⭐⭐] [⭐⭐⭐⭐⭐]  │
└─────────────────────────────────────┘
```

View the blueprint:
```bash
hermes-feedback gateway blueprint
```

## Installation

```bash
mkdir -p ~/.hermes/scripts ~/.hermes/feedback/patterns ~/.hermes/skills/hermes/feedback-rate

cp scripts/*.py ~/.hermes/scripts/
cp patterns/patterns.json ~/.hermes/feedback/patterns/
cp patterns/prompts/* ~/.hermes/feedback/patterns/prompts/
cp skill/SKILL.md ~/.hermes/skills/hermes/feedback-rate/

# Make scripts executable
chmod +x ~/.hermes/scripts/*.py

# Add to PATH (optional)
echo 'export PATH="$HOME/.hermes/scripts:$PATH"' >> ~/.bashrc

# Weekly analysis cron
hermes cron add --name feedback-analyze \
  --schedule "0 8 * * 1" \
  --script ~/.hermes/scripts/analyze.py \
  --prompt "Analyze feedback trends and surface insights from ratings.ndjson"
```

## Related Projects

- [hermes-brain](https://github.com/zedarvates/hermes-brain) — Cognitive architecture
- [kitten-tts](https://github.com/zedarvates/kitten-tts) — Local French TTS
- [ultra-pipeline-framework](https://github.com/zedarvates/ultra-pipeline-framework) — DAG pipeline orchestration

## License

MIT


---

[![Donate](https://img.shields.io/badge/☕%20Soutenir-BTC%20%7C%20ETH-orange)](DONATE.md)