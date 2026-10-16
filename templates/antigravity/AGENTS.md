{{include shared/RULES.md}}

## Orchestration (Antigravity)
- The roles are custom agents in `.agents/agents/*.md` with `subagent: true`: `ops-lead`, `aks-architect`, `sre`, `iac-engineer`, `k8s-engineer`, `validator`, `secops`, `reviewer`.
- The primary agent is the orchestrator. It spawns them with `invoke_subagent`, following the Orchestrator rules above.
- Antigravity has no command hook in this template: before running any cluster or Azure command, check it with `python3 .agents/hooks/aks_guard.py --check "<command>"` and don't run it if it prints `BLOCKED`.
