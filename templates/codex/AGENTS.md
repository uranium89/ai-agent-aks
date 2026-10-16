{{include shared/RULES.md}}

## Orchestration (Codex)
- The roles are custom agents in `.codex/agents/*.toml`: `ops-lead`, `aks-architect`, `sre`, `iac-engineer`, `k8s-engineer`, `validator`, `secops`, `reviewer`.
- The main thread is the orchestrator. Spawn ONE subagent per step, following the Orchestrator rules above.
- `.codex/hooks.json` runs `.codex/hooks/aks_guard.py` before every shell command; blocked commands fail with `BLOCKED by aks-guard`.
- Subagents inherit the parent's sandbox and approval policy; role write zones are enforced only by these instructions.
