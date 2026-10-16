# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Templates for an AI platform team for Azure Kubernetes Service (ops-lead, aks-architect, sre, iac-engineer, k8s-engineer, validator, secops, reviewer) working for a technical operator, packaged for Claude Code, Codex, Cursor, OpenCode and Antigravity. It follows the architecture of ai-scrum-team. The workflow rules live in `shared/RULES.md`; this file is about maintaining the templates, not running the workflow.

## Commands

- `python3 scripts/build.py`: regenerate `dist/` from `shared/` + `templates/`.
- `python3 scripts/build.py --check`: exit 1 if `dist/` is stale. Run it after every change.
- `python3 -m unittest discover -s tests`: test the command guard. Run it after every change to `shared/hooks/aks_guard.py`.
- `python3 shared/hooks/aks_guard.py --check "<command>"`: see the guard's verdict for one command.

Everything needs only the Python standard library (3.9+).

## Architecture

- `shared/` holds everything common to all tools: `RULES.md`, the eight agent prompts (`shared/agents/*.md`, front matter holds only `description`), the command guard (`shared/hooks/aks_guard.py`), README sections (`shared/docs/`), and the project skeleton plus example incident (`shared/project/`, copied into every `dist/<tool>/aks-team/`).
- `templates/<tool>/` mirrors the output layout exactly and holds only tool-specific parts: agent front matter or TOML fields, hook wiring, the rules-file wrapper and its "Orchestration" section, and the README.
- `templates/` files pull in shared content with `{{include PATH}}`, `{{body PATH}}` and `{{description PATH}}`. Never write those three directive strings literally inside `aks_guard.py`.
- `dist/` is generated output. Never edit it by hand.

## Conventions

- All prompts, rules and templates are written in English. Reports to the operator follow the language recorded in `aks-team/ENVIRONMENT.md`.
- Put a change in `shared/` whenever it applies to more than one tool.
- The core safety property: agents never change a cluster or Azure resource and never read secrets. Any change to roles, prompts or the guard must keep it. When you allow a new command in the guard, add it to `ALLOWED` in `tests/test_aks_guard.py`; when you block one, add it to `BLOCKED`.
- Tool config formats (front matter fields, model IDs, hook formats) change often. Check the tool's official docs before editing them; the Antigravity `tools` list and `commandExecutionPolicy` values are unverified beyond the documented ones.
- A role's write zone, model tier (strong or fast) and duties must agree across `shared/RULES.md`, `shared/docs/WORKFLOW.md`, the agent prompt and every tool's agent wrapper. For OpenCode, bash rules use last-match-wins.
