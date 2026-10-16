---
description: {{description shared/agents/aks-architect.md}}
mode: subagent
model: anthropic/claude-opus-5-5
temperature: 0.1
permission:
  edit: allow
  webfetch: allow
  bash:
    "*": ask
    "rg *": allow
    "ls*": allow
    "cat *": allow
    "git status*": allow
    "git diff*": allow
    "git log*": allow
    "command -v *": allow
    "kubectl --context * get *": allow
    "kubectl --context * describe *": allow
    "kubectl --context * logs *": allow
    "kubectl --context * top *": allow
    "kubectl --context * events*": allow
    "kubectl --context * auth can-i *": allow
    "kubectl --context * api-resources*": allow
    "kubectl --context * version*": allow
    "kubectl --context * rollout status *": allow
    "kubectl --context * rollout history *": allow
    "kubectl config get-contexts*": allow
    "az * show *": allow
    "az * list *": allow
    "az aks get-upgrades *": allow
    "az aks get-versions *": allow
    "az monitor log-analytics query *": allow
    "az graph query *": allow
    "helm --kube-context * list*": allow
    "helm --kube-context * status *": allow
    "helm --kube-context * history *": allow
    "flux --context * get *": allow
    "git push*": deny
---

{{body shared/agents/aks-architect.md}}
