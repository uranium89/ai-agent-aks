# AI AKS Team

An AI platform team for Azure Kubernetes Service, built on the architecture of [ai-scrum-team](https://github.com/uranium89/ai-scrum-team): eight role agents (ops-lead, aks-architect, sre, iac-engineer, k8s-engineer, validator, secops, reviewer) hand work to each other through files in `aks-team/`. They troubleshoot live clusters, write and review Terraform/Bicep, manifests, Helm and GitOps config, and run audits (security, upgrade readiness, cost, reliability).

**The agents are read-only against clusters and Azure.** They diagnose, plan, implement in the repo and validate with previews (`terraform plan`, `what-if`, `kubectl diff`); every change to a cluster comes to you as a reviewed `runbook.md` with pre-checks, steps, verification and rollback. You stay the only one who changes production.

Packaged for five AI coding tools.

## Use a template

Pick your tool and copy the contents of its `dist/` folder, including hidden folders, into the root of your platform repository:

| Tool | Copy from | Rules file | Agents | Command guard |
|---|---|---|---|---|
| Claude Code | `dist/claude/` | `CLAUDE.md` | `.claude/agents/*.md` | `PreToolUse` hook in `.claude/settings.json` |
| OpenAI Codex | `dist/codex/` | `AGENTS.md` | `.codex/agents/*.toml` | `PreToolUse` hook in `.codex/hooks.json` |
| Cursor | `dist/cursor/` | `.cursor/rules/aks-team.mdc` | `.cursor/agents/*.md` | `beforeShellExecution` hook in `.cursor/hooks.json` |
| OpenCode | `dist/opencode/` | `AGENTS.md` | `.opencode/agents/*.md` | plugin `.opencode/plugins/aks-guard.js` |
| Google Antigravity | `dist/antigravity/` | `AGENTS.md` | `.agents/agents/*.md` | none (instructions only) |

```sh
cp -R dist/claude/. /path/to/your-platform-repo/
```

```
your-platform-repo/
├── CLAUDE.md / AGENTS.md        rules file (tool-specific)
├── .claude/ agents/ hooks/ settings.json   agents and command guard (tool-specific)
├── aks-team/                    everything the AI team writes about the work
│   ├── README.md  ACCESS.md     prompts; how to set up read-only access
│   ├── ENVIRONMENT.md           clusters, contexts, guardrails, inventory
│   ├── ARCHITECTURE.md  adr/    architecture, conventions, quality gates
│   ├── work/W-NNN-<slug>/       one folder per incident, change or audit
│   ├── decisions/  runbooks/  reports/  backlog/  RISKS.md
└── infra/, k8s/, charts/, clusters/ ...   your IaC, manifests and GitOps config
```

## Quick start

1. **Read-only access** (once): follow `aks-team/ACCESS.md` to give the agents an identity and kubeconfig that cannot write, and start your tool from that shell.
2. **Kickoff** (Claude Code example):
   ```
   Kick off the AKS team for this repository.
   Act as the orchestrator defined in CLAUDE.md and run the Kickoff.
   Invoke each agent as a subagent, one at a time.
   Ask me the interview questions and wait for my answers. Then finish the Kickoff and show me the inventory, the backlog, the top risks and any decision briefs.
   ```
3. **Daily work**:
   ```
   incident: api pods crash-looping in namespace shop on prod since 09:40 UTC
   change: add a spot user node pool for batch jobs on dev, then prod
   audit: upgrade on all environments
   ask: why is pod payments-worker-0 Pending on dev?
   quick: raise memory request of api to 512Mi on dev
   verify W-012
   ```

Each tool's `aks-team/README.md` has the exact prompts and notes for that tool.

## How it differs from ai-scrum-team

| ai-scrum-team | AI AKS team |
|---|---|
| Builds a product for a non-technical stakeholder | Supports a technical operator who owns AKS clusters |
| Sprints of user stories | Work items: incident, change, audit (+ `ask:`, `quick:`, `verify`) |
| product-owner, architect, coder, tester, devsecops, reviewer, ui-designer | ops-lead, aks-architect, sre, iac-engineer, k8s-engineer, validator, secops, reviewer |
| Never deploy | Never change a cluster or Azure; read-only investigation; runbooks for the operator |
| Tests + security gate + review | Offline validation + read-only previews + security gate + blast-radius/rollback review |
| Instructions only | Plus a command guard hook (`aks_guard.py`) and a read-only identity |

## The command guard

`shared/hooks/aks_guard.py` (standard-library Python 3.9+) inspects every shell command an agent runs and blocks:
- writes to clusters and Azure: `kubectl apply/delete/scale/drain/exec/...`, `helm install/upgrade/rollback`, `terraform apply/destroy/import/state rm`, `az ... create/update/delete/upgrade/...`, `az aks command invoke`, `flux reconcile`, `argocd app sync`, ...;
- secret reads: `kubectl get secret -o yaml`, `helm get values/manifest`, `az keyvault secret show`, `az aks get-credentials`, `az account get-access-token`, kubeconfig / `~/.azure*` / `*.tfstate` files, secret environment variables;
- default switching and untargeted commands: `kubectl config use-context`, `kubectx`, `az account set`, and any cluster command without `--context` / `--kube-context`;
- commands that never exit: `-w`, `--watch`, `logs -f`, `watch`.

It also looks inside `bash -c`, `xargs`, `find -exec`, pipes and `&&` chains. Previews stay allowed (`--dry-run`, `kubectl diff`, `helm template`, `terraform plan`, `az deployment what-if`).

```sh
python3 shared/hooks/aks_guard.py --check "kubectl --context prod rollout restart deploy/api"
# BLOCKED by aks-guard: kubectl rollout restart changes workloads. ...
```

It is a guardrail, not a security boundary. The read-only identity in `ACCESS.md` is the boundary.

## Repository layout

```
shared/       content common to every tool (edit here first)
  RULES.md      roles, hard limits, kickoff, work item flows, risk process, runbook format, quality gates
  agents/       the eight agent prompts (description + body)
  hooks/        aks_guard.py, the command guard
  docs/         README sections included in every tool's README
  project/      the aks-team/ skeleton + example incident (W-000)
templates/    tool-specific parts only: front matter, hook config, orchestration notes, README
dist/         generated, ready-to-copy templates (do not edit by hand)
scripts/build.py
tests/        guard tests
```

## Edit a template

1. Change shared content in `shared/`, and tool-specific content in `templates/<tool>/`.
2. Run `python3 scripts/build.py` to regenerate `dist/`.
3. Run `python3 scripts/build.py --check` and `python3 -m unittest discover -s tests`.

Directives in `templates/` files: `{{include PATH}}` (whole file), `{{body PATH}}` (agent prompt without front matter), `{{description PATH}}` (the agent's `description:`).

## Tóm tắt (Tiếng Việt)

Bộ template "đội AI cho AKS" dựa trên kiến trúc ai-scrum-team: 8 agent chuyên trách phối hợp qua file trong `aks-team/`, hỗ trợ troubleshoot cluster, viết/review Terraform/Bicep, manifest/Helm/GitOps, và audit (bảo mật, upgrade, chi phí, độ tin cậy). Agent **chỉ đọc** cluster và Azure; mọi thay đổi được giao cho bạn dưới dạng `runbook.md` đã review (pre-check, các bước, verify, rollback). Bắt đầu bằng `aks-team/ACCESS.md` (tạo identity read-only), rồi chạy prompt Kickoff. Ghi câu trả lời "Report language: Vietnamese" khi phỏng vấn để agent báo cáo bằng tiếng Việt.
