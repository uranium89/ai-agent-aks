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

## Prompts for daily work

| You say | What happens |
|---|---|
| `incident: <symptom> on <environment>` | ops-lead triages, sre diagnoses read-only, reviewer checks any production remediation, you get `summary.md` + `runbook.md` |
| `change: <what> on <environments>` | plan -> (threat model) -> IaC / manifests -> validation with previews -> security gate -> review -> you get a reviewed PR-ready change and a runbook |
| `audit: <security / upgrade / cost / reliability / networking / observability / full> on <environments>` | read-only evidence -> prioritized recommendations -> challenge -> report and new backlog items |
| `ask: <question>` | a quick read-only answer with evidence, no paperwork |
| `quick: <small change>` | a short change flow for low-risk, non-production edits; the gates still run |
| `verify W-NNN` | after you applied a runbook: sre checks the result read-only |

## The team

| Agent | Model | Job |
|---|---|---|
| ops-lead | strong | Interviews you at kickoff, turns requests into work items, accepts work against evidence, writes short summaries |
| aks-architect | strong | Owns `aks-team/ARCHITECTURE.md` and ADRs, writes change plans with blast radius and rollback, turns audit findings into recommendations |
| sre | strong | Investigates clusters and Azure read-only: incident diagnosis, discovery, upgrade/capacity/cost evidence, post-change verification |
| iac-engineer | fast | Implements Terraform / Bicep steps, validates offline, writes the runbook |
| k8s-engineer | fast | Implements manifest / Helm / Kustomize / GitOps steps, validates offline, writes the runbook |
| validator | fast | Proves every acceptance criterion with offline checks and read-only previews; hunts unexpected destroys and restarts |
| secops | strong | Security gate on IaC and manifests, threat models, live posture audits, CI and scanner config |
| reviewer | strong | Reviews changes, runbooks and audit reports for correctness, blast radius and rollback |

## What you do as the operator

1. **Set up read-only access once** (`aks-team/ACCESS.md`) and start your AI tool from that shell.
2. **Answer the kickoff interview**: clusters and contexts, which are production, how changes are delivered, constraints.
3. **Choose options in decision briefs** (`aks-team/decisions/DEC-*.md`) for 🔴 decisions.
4. **Run the runbooks** (`aks-team/work/W-*/runbook.md`) — usually by merging the PR and letting your pipeline or GitOps apply it — then say `verify W-NNN`.

The agents never change a cluster or an Azure resource. You stay the only one who does.

## How work flows

```
Kickoff (once): tooling -> interview -> read-only discovery -> architecture baseline -> security gates -> backlog
Incident: triage -> sre diagnosis -> (reviewer remediation check) -> summary + runbook -> you apply -> verify
Change:   request -> plan -> (threat model) -> IaC / K8s -> validation -> security gate -> review -> acceptance -> you apply -> verify
          NEEDS_FIX: Route ENGINEER (small fix) or Route ARCHITECT (plan wrong), max 3 loops, then Blocked
Audit:    scope -> sre / secops evidence -> architect recommendations -> reviewer challenge -> report + backlog
```

## Risk levels

| Level | Example | Who decides |
|---|---|---|
| 🟢 | A label, a resource request in dev, a dashboard | The agent, recorded in the plan |
| 🟡 | Pod restarts, a new add-on, node pool change outside prod, PDB/HPA in prod | Architect proposes, reviewer challenges; escalated to you if they disagree |
| 🔴 | Prod disruption, version upgrades in prod, networking, identity/RBAC, data/PV deletion, recreation, recurring cost | You, through a decision brief; the item waits |

## Safety layers

1. **Read-only identity** (`aks-team/ACCESS.md`): the real boundary. Without it, the agents run with your own permissions.
2. **Command guard** (`aks_guard.py`, wired as a hook where the tool supports it): blocks cluster/Azure write commands, Secret reads, credential files, context switches, and commands without an explicit `--context`.
3. **Rules and prompts**: every agent is told it is read-only and must write runbooks instead.
4. **Review gates**: validator previews, secops scanners and the reviewer's blast-radius and rollback check before anything reaches you.

## Caveats

- Role write zones are instructions to the model; the tools don't enforce them.
- The command guard parses shell commands; a determined bypass (an unlisted tool, a script file the agent wrote) can get past it. That's why the read-only identity matters.
- Scanners and previews catch known misconfigurations and diffs, not every outage. Rollback plans are reviewed, not rehearsed.
- AKS changes fast (versions, retirements, preview features). Agents are told to check Microsoft Learn and cite it; treat uncited claims as unverified.
- Cost: five agents use a strong model. Use `ask:` and `quick:` for small things.

## OpenCode notes
- Guard: `.opencode/plugins/aks-guard.js` runs `.opencode/hooks/aks_guard.py` before every bash command and fails closed if it can't run (needs `python3`). Test it with `kubectl get pods` (no `--context`): it must be blocked.
- Bash permissions (the last matching pattern wins):
  - ops-lead: only `rg`, `ls`, `cat`, `git status/diff/log`, `command -v`.
  - aks-architect, reviewer, sre: those plus read-only `kubectl --context ...`, `az ... show/list`, `helm --kube-context ... list/status/history`, `flux --context ... get`; anything else asks you.
  - secops: the same plus the scanners.
  - iac-engineer, k8s-engineer, validator: any command, still filtered by the guard; `git push` is denied for everyone.
- Models: `anthropic/claude-opus-5-5` for the strong roles, `anthropic/claude-sonnet-5-5` for the engineers and validator.
- If a project has both `CLAUDE.md` and `AGENTS.md`, OpenCode reads only `AGENTS.md`.
