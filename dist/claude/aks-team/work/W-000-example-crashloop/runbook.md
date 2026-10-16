# Runbook W-000: roll back api to 2.7.3
Risk: 🟡   Environments: aks-prod-weu (your admin context)   Expected disruption: rolling restart of `api`, no downtime (old replica keeps serving)
Maintenance window needed: no   Estimated duration: 10 minutes

## Pre-checks
1. `kubectl --context aks-prod-weu -n shop get deploy api -o jsonpath='{.spec.template.spec.containers[0].image}'`
   -> expect: `.../api:2.8.0`
2. `flux --context aks-prod-weu get kustomizations -n flux-system apps`
   -> expect: `Ready True`, revision of the commit with PR #412

## Steps
1. Revert PR #412 in the GitOps repo and merge the revert (normal review rules apply).
2. Let Flux sync (default interval 5m), or trigger it: `flux --context aks-prod-weu reconcile kustomization apps -n flux-system --with-source`
   -> expect: `applied revision main@sha1:<revert commit>`

## Verify
1. `kubectl --context aks-prod-weu-ro -n shop rollout status deploy/api --timeout=5m`
   -> expect: `successfully rolled out`
2. `kubectl --context aks-prod-weu-ro -n shop get pods -l app=api`
   -> expect: 3/3 Running, image 2.7.3, restarts 0 after 10 minutes

## Rollback
Trigger: the revert makes things worse (new errors, fewer Ready replicas).
1. Revert the revert commit and merge; Flux re-applies 2.8.0 (the current, partly working state).
