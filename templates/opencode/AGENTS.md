{{include shared/RULES.md}}

## Orchestration (OpenCode)
- The roles are subagents in `.opencode/agents/*.md`: `ops-lead`, `aks-architect`, `sre`, `iac-engineer`, `k8s-engineer`, `validator`, `secops`, `reviewer`.
- The primary agent (Build) is the orchestrator. It invokes them via the Task tool, following the Orchestrator rules above; the operator can also @mention them.
- `.opencode/plugins/aks-guard.js` runs `.opencode/hooks/aks_guard.py` before every bash command; blocked commands fail with `BLOCKED by aks-guard`.
