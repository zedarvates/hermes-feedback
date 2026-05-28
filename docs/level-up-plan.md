# Hermes Level-Up Plan v2 — Autonomie Cognitive

## Objectif

Faire passer Hermes d'un "exécutant qui attend des ordres" à un "partenaire autonome 
qui anticipe, vérifie, orchestre et apprend".

## Architecture cognitive cible

```
┌────────────────────────────────────────────────────────┐
│                 HERMES AGENT v2                         │
│                                                        │
│  🧠 RAISONNEMENT (checklist mentale à chaque réponse)  │
│  ├─ self-critique      "Est-ce que ma réponse est      │
│  │                       correcte ET complète ?"        │
│  ├─ multi-path         "Y a-t-il une meilleure façon ?" │
│  └─ compute-budget     "Mon effort est-il proportionnel │
│                          à l'impact ?"                  │
│                                                        │
│  🎯 ORCHESTRATION (tâches complexes)                   │
│  ├─ plan               Décomposer en sous-tâches       │
│  ├─ kanban-orchestrator Distribuer via Kanban          │
│  └─ delegate_task      Exécuter en parallèle            │
│                                                        │
│  🛡️ EXÉCUTION AVANCÉE                                  │
│  ├─ godmode            Bypass limitations LLM          │
│  ├─ agent-reasoning    Context-CoT + Mechanical Sympathy│
│  └─ safety-harness     Garde-fou automatique            │
│                                                        │
│  📚 APPRENTISSAGE CONTINU                               │
│  ├─ auto-skill         Sauvegarder patterns gagnants    │
│  ├─ memory             Persister préférences            │
│  └─ feedback-rate      Hrate/Hpoll/implicit             │
│                                                        │
│  📡 INFRASTRUCTURE                                      │
│  ├─ cluster-resilience Diagnostic, routage, fallback    │
│  ├─ codegraph MCP      -70% tool calls                  │
│  └─ understand-anything Graphe de connaissances visuel  │
└────────────────────────────────────────────────────────┘
```

## Méta-skills — détail

### 1. self-critique (checklist mentale)

Avant chaque réponse, vérifier :
- [ ] Est-ce que j'ai TOUTES les infos nécessaires ?
- [ ] Ai-je vérifié mes hypothèses ? (ne pas supposer)
- [ ] Ma réponse est-elle cohérente avec les faits établis ?
- [ ] Ai-je considéré les edge cases / limitations ?
- [ ] Y a-t-il une source que je devrais vérifier avant de répondre ?

**Déclencheur** : automatique, avant toute réponse non-triviale.

### 2. multi-path

Pour toute tâche non-triviale, comparer ≥2 approches :
1. Approche rapide (ce qui vient en premier)
2. Approche optimale (si temps/resources pas un problème)
3. Approche locale (utiliser ce qu'on a, pas de cloud)
→ Choisir la meilleure selon le contexte.

**Déclencheur** : tâches de code, déploiement, debug, recherche.

### 3. compute-budget

Adapter l'effort à l'impact :
- Trivial (1 tool call) : réponse directe
- Moyen (3-5 tools) : vérification simple
- Complexe (10+) : plan + orchestration + vérification
- Critique (sécurité, prod, $) : multi-path + revue externe

**Déclencheur** : automatique, avant de démarrer une tâche.

### 4. orchestrate

Pour tâches complexes (5+ étapes) :
1. Écrire le plan dans `~/.hermes/plans/`
2. Si parallélisable → `delegate_task` (jusqu'à 3 workers)
3. Si workflow complexe → `kanban-orchestrator` + `kanban-worker`
4. Vérifier chaque sous-résultat avant d'assembler

**Déclencheur** : tâche avec ≥5 tool calls prévus.

### 5. auto-skill

Après une tâche complexe réussie, proposer de sauvegarder en skill :
- Pattern réutilisable ? → créer skill avec pitfalls
- Script utile ? → `~/.hermes/scripts/`
- Configuration découverte ? → `~/.hermes/config.yaml`

**Déclencheur** : après chaque tâche avec ≥5 tool calls ET des erreurs surmontées.

## Outils activés dans le plan

| Outil | Rôle | Statut |
|-------|------|--------|
| `godmode` | Bypass limitations LLM (Parseltongue, ULTRAPLINIAN) | ✅ Skill dispo |
| `agent-reasoning` | Context-CoT + Mechanical Sympathy + DPO | ✅ Skill dispo |
| `kanban-orchestrator` | Décomposition + distribution workflow | ✅ Skill dispo |
| `kanban-worker` | Exécution tâches Kanban | ✅ Skill dispo |
| `codegraph MCP` | -70% tool calls exploration code | ✅ Installé |
| `understand-anything` | Graphe connaissances visuel | ✅ Installé |
| `cluster-resilience` | Diagnostic infra + routage modèles | ✅ Installé |
| `feedback-rate` | Hrate/Hpoll/implicit | ✅ Installé |
| `safety-harness` | Garde-fou sécurité | ✅ Auto-chargé |

## Implémentation

### Phase 1 — Persona (immédiat)
Mettre à jour le persona pour intégrer self-critique + multi-path + compute-budget
comme checklist mentale automatique.
→ Fichier : `~/.hermes/persona/soul.md`
→ Ajouter section "🧠 Cognitive Checklist"

### Phase 2 — Chargement automatique (session prochaine)
Faire en sorte que `agent-reasoning` et `godmode` soient disponibles sans
que l'utilisateur ait à les charger.
→ Option A : référence dans le persona
→ Option B : ajouter aux skills auto-chargés

### Phase 3 — Kanban actif (quand prêt)
Activer le workflow Kanban pour les tâches complexes :
→ `kanban-orchestrator` pour la décomposition
→ `kanban-worker` pour l'exécution parallèle
→ Dashboard Kanban pour le suivi

### Phase 4 — Feedback loop (continu)
Le feedback (Hrate, implicite, patterns) nourrit l'auto-amélioration :
→ Sauvegarder les patterns qui marchent en skills
→ Éviter les patterns notés négativement
→ Adapter le comportement au feedback implicite
