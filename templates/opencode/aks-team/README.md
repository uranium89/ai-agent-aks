# AI AKS Team for OpenCode

## Setup
1. Copy everything in the template folder (`dist/opencode/`, the parent of this `aks-team/` folder), including the hidden `.opencode/`, into the root of your platform repository (the one with your Terraform/Bicep, manifests or GitOps config).
2. Set up read-only access as described in `aks-team/ACCESS.md`, and start OpenCode from that shell.
3. Run the kickoff below.

## Prompts
**Kickoff** (once per repository):
```
Kick off the AKS team for this repository.
Act as the orchestrator defined in AGENTS.md and run the Kickoff.
Invoke each subagent via the Task tool, one at a time.
Ask me the interview questions and wait for my answers. Then finish the Kickoff and show me the inventory, the backlog, the top risks and any decision briefs.
```

**Daily work** (the rules file defines each keyword; add the line "Invoke each subagent via the Task tool, one at a time." if the tool doesn't delegate on its own):
```
incident: api pods crash-looping in namespace shop on prod since 09:40 UTC
change: add a spot user node pool for batch jobs on dev, then prod
audit: upgrade on all environments
ask: why is pod payments-worker-0 Pending on dev?
quick: raise memory request of api to 512Mi on dev
verify W-012
```

{{include shared/docs/WORKFLOW.md}}

## OpenCode notes
- Guard: `.opencode/plugins/aks-guard.js` runs `.opencode/hooks/aks_guard.py` before every bash command and fails closed if it can't run (needs `python3`). Test it with `kubectl get pods` (no `--context`): it must be blocked.
- Bash permissions (the last matching pattern wins):
  - ops-lead: only `rg`, `ls`, `cat`, `git status/diff/log`, `command -v`.
  - aks-architect, reviewer, sre: those plus read-only `kubectl --context ...`, `az ... show/list`, `helm --kube-context ... list/status/history`, `flux --context ... get`; anything else asks you.
  - secops: the same plus the scanners.
  - iac-engineer, k8s-engineer, validator: any command, still filtered by the guard; `git push` is denied for everyone.
- Models: `anthropic/claude-opus-5-5` for the strong roles, `anthropic/claude-sonnet-5-5` for the engineers and validator.
- If a project has both `CLAUDE.md` and `AGENTS.md`, OpenCode reads only `AGENTS.md`.
