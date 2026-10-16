# AI AKS Team for Cursor

## Setup
1. Copy everything in the template folder (`dist/cursor/`, the parent of this `aks-team/` folder), including the hidden `.cursor/`, into the root of your platform repository (the one with your Terraform/Bicep, manifests or GitOps config).
2. Set up read-only access as described in `aks-team/ACCESS.md`, and start Cursor from that shell.
3. Run the kickoff below.

## Prompts
**Kickoff** (once per repository):
```
Kick off the AKS team for this repository.
Act as the orchestrator defined in .cursor/rules/aks-team.mdc and run the Kickoff.
Invoke each agent with its slash command (/ops-lead, /sre, ...), one at a time.
Ask me the interview questions and wait for my answers. Then finish the Kickoff and show me the inventory, the backlog, the top risks and any decision briefs.
```

**Daily work** (the rules file defines each keyword; add the line "Invoke each agent with its slash command (/ops-lead, /sre, ...), one at a time." if the tool doesn't delegate on its own):
```
incident: api pods crash-looping in namespace shop on prod since 09:40 UTC
change: add a spot user node pool for batch jobs on dev, then prod
audit: upgrade on all environments
ask: why is pod payments-worker-0 Pending on dev?
quick: raise memory request of api to 512Mi on dev
verify W-012
```

{{include shared/docs/WORKFLOW.md}}

## Cursor notes
- Guard: `.cursor/hooks.json` runs `.cursor/hooks/aks_guard.py --cursor` before every shell command. It returns `deny` for blocked commands, `allow` for commands made only of read-only cluster and helper tools, and `ask` for everything else. Test it with `kubectl get pods` (no `--context`): it must be denied.
- Models: strong roles use `claude-opus-5[effort=high]`, the engineers and validator `composer-2`. Set `model: inherit` to use the main session's model.
- Every agent has `readonly: false` because each must write its own output file, so write zones are only instructions.
- Cursor also reads `.claude/agents/`. If the project has both, `.cursor/agents/` wins on name conflicts.
