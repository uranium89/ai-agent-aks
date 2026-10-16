# AI AKS Team for Claude Code

## Setup
1. Copy everything in the template folder (`dist/claude/`, the parent of this `aks-team/` folder), including the hidden `.claude/`, into the root of your platform repository (the one with your Terraform/Bicep, manifests or GitOps config).
2. Set up read-only access as described in `aks-team/ACCESS.md`, and start Claude Code from that shell.
3. Run the kickoff below.

## Prompts
**Kickoff** (once per repository):
```
Kick off the AKS team for this repository.
Act as the orchestrator defined in CLAUDE.md and run the Kickoff.
Invoke each agent as a subagent, one at a time.
Ask me the interview questions and wait for my answers. Then finish the Kickoff and show me the inventory, the backlog, the top risks and any decision briefs.
```

**Daily work** (the rules file defines each keyword; add the line "Invoke each agent as a subagent, one at a time." if the tool doesn't delegate on its own):
```
incident: api pods crash-looping in namespace shop on prod since 09:40 UTC
change: add a spot user node pool for batch jobs on dev, then prod
audit: upgrade on all environments
ask: why is pod payments-worker-0 Pending on dev?
quick: raise memory request of api to 512Mi on dev
verify W-012
```

{{include shared/docs/WORKFLOW.md}}

## Claude Code notes
- Guard: `.claude/settings.json` registers `.claude/hooks/aks_guard.py` as a `PreToolUse` hook on Bash (needs `python3` on PATH) and denies `Read` on `~/.kube/`, `~/.azure*/` and `*.tfstate`. Test it: ask Claude to run `kubectl get pods` (no `--context`); it must be blocked. If you keep your own `.claude/settings.json`, merge these keys instead of overwriting.
- Models: ops-lead, aks-architect, sre, secops and reviewer use `model: opus`; iac-engineer, k8s-engineer and validator use `model: sonnet`.
- Run `/agents` to confirm all eight agents are listed, and `/hooks` to confirm the guard.
- For a reviewer from a different vendor, run the review step in another tool (for example the Codex or OpenCode template) on the same repo.
