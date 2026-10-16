# AI AKS Team for OpenAI Codex

## Setup
1. Copy everything in the template folder (`dist/codex/`, the parent of this `aks-team/` folder), including the hidden `.codex/`, into the root of your platform repository (the one with your Terraform/Bicep, manifests or GitOps config).
2. Set up read-only access as described in `aks-team/ACCESS.md`, and start OpenAI Codex from that shell.
3. Run the kickoff below.

## Prompts
**Kickoff** (once per repository):
```
Kick off the AKS team for this repository.
Act as the orchestrator defined in AGENTS.md and run the Kickoff.
Spawn subagent for each step, one at a time, and wait for it to finish.
Ask me the interview questions and wait for my answers. Then finish the Kickoff and show me the inventory, the backlog, the top risks and any decision briefs.
```

**Daily work** (the rules file defines each keyword; add the line "Spawn subagent for each step, one at a time, and wait for it to finish." if the tool doesn't delegate on its own):
```
incident: api pods crash-looping in namespace shop on prod since 09:40 UTC
change: add a spot user node pool for batch jobs on dev, then prod
audit: upgrade on all environments
ask: why is pod payments-worker-0 Pending on dev?
quick: raise memory request of api to 512Mi on dev
verify W-012
```

{{include shared/docs/WORKFLOW.md}}

## Codex notes
- Guard: `.codex/hooks.json` registers `.codex/hooks/aks_guard.py` as a `PreToolUse` hook. Project hooks load only when the project's `.codex/` is trusted: run `/hooks` once to review and trust it. Test it by asking for `kubectl get pods` without `--context`; it must be blocked.
- Codex only spawns subagents when asked explicitly, so the prompts say "Spawn subagent".
- Subagents share the main session's sandbox and approval policy. The sandbox must allow network access for `kubectl` and `az`; keep approvals on for anything outside the workspace.
- Models: strong roles use `model_reasoning_effort = "high"`, iac-engineer, k8s-engineer and validator `"medium"`. To pin a model, uncomment the `model` line.
