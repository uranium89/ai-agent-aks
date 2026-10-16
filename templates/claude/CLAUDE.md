# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

{{include shared/RULES.md}}

## Orchestration (Claude Code)
- The roles are subagents in `.claude/agents/*.md`: `ops-lead`, `aks-architect`, `sre`, `iac-engineer`, `k8s-engineer`, `validator`, `secops`, `reviewer`.
- The main session is the orchestrator. Invoke the agents with the Agent tool, following the Orchestrator rules above.
- `.claude/settings.json` runs `.claude/hooks/aks_guard.py` before every Bash command (blocked commands fail with `BLOCKED by aks-guard`) and denies reading kubeconfig, Azure login and Terraform state files.
- Agent front matter uses the aliases `model: opus` / `model: sonnet`, which resolve to the current model in each family.
