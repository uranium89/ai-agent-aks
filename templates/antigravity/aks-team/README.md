# AI AKS Team for Google Antigravity

## Setup
1. Copy everything in the template folder (`dist/antigravity/`, the parent of this `aks-team/` folder), including the hidden `.agents/`, into the root of your platform repository (the one with your Terraform/Bicep, manifests or GitOps config).
2. Set up read-only access as described in `aks-team/ACCESS.md`, and start Google Antigravity from that shell.
3. Run the kickoff below.

## Prompts
**Kickoff** (once per repository):
```
Kick off the AKS team for this repository.
Act as the orchestrator defined in AGENTS.md and run the Kickoff.
Use invoke_subagent for each step, one at a time.
Ask me the interview questions and wait for my answers. Then finish the Kickoff and show me the inventory, the backlog, the top risks and any decision briefs.
```

**Daily work** (the rules file defines each keyword; add the line "Use invoke_subagent for each step, one at a time." if the tool doesn't delegate on its own):
```
incident: api pods crash-looping in namespace shop on prod since 09:40 UTC
change: add a spot user node pool for batch jobs on dev, then prod
audit: upgrade on all environments
ask: why is pod payments-worker-0 Pending on dev?
quick: raise memory request of api to 512Mi on dev
verify W-012
```

{{include shared/docs/WORKFLOW.md}}

## Antigravity notes (verify on first run)
- **No enforced guard.** This template has no command hook, so the read-only identity from `aks-team/ACCESS.md` is required, not optional. The rules tell agents to check commands with `.agents/hooks/aks_guard.py --check`, but that is an instruction, not enforcement.
- `commandExecutionPolicy`: ops-lead, aks-architect and reviewer use `sandbox`; sre, secops, the engineers and validator use `auto` so they can reach the cluster and run scanners. Switch them to a policy that asks you first if your Antigravity version offers one.
- `tools` lists the four tool names from the official docs: `view_file`, `grep_search`, `replace_file_content`, `run_command`. An unknown tool name can hang a subagent; if one hangs, check this list first.
- Models: `pro` for the strong roles, `flash` for the engineers and validator.
