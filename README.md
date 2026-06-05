# Hermes Feedback 📊

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Status](https://img.shields.io/badge/status-active-brightgreen.svg)]()

Token-optimized feedback system for Hermes Agent — zero-LLM patterns, polls, implicit signals, DPO export.

## Features

- **Zero-LLM feedback** — Implicit signals (usage, time, retries) without token cost
- **Polls & ratings** — Quick user feedback with minimal friction
- **DPO export** — Export feedback as DPO pairs for fine-tuning
- **Multi-channel** — Telegram, Discord, CLI, web

## Workflow Patterns

Le feedback system utilise 2 des 6 patterns de workflows dynamiques :

### Generate and Filter
Sur-génère des suggestions → filtre par feedback utilisateur implicite :
```
Agent → Génère N suggestions → Feedback implicite → Top-K conservés
```

### Adversarial Verification
Un second agent vérifie la qualité du feedback :
```
Agent A → Propose amélioration → Agent B → Vérifie → Valide/Rejette
```

## Intégration Hermes

Le skill `hermes-feedback` est disponible dans Hermes :
```
~/.hermes/skills/feedback/
├── feedback-memory.jsonl   — Journal de feedback
├── polls/                  — Sondes de satisfaction
└── export/                 — Export DPO
```

## Projets liés

- [hermes-brain](https://github.com/zedarvates/hermes-brain) — Architecture cognitive
- [kitten-tts](https://github.com/zedarvates/kitten-tts) — TTS local FR
- [ultra-pipeline-framework](https://github.com/zedarvates/ultra-pipeline-framework) — Pipeline DAG

## Licence MIT
