# Diagnosis W-000

## Summary
`api` v2.8.0 uses about 40% more memory at startup than v2.7.3 and exceeds its 256Mi limit, so the kernel OOM-kills it during warm-up. Nodes are healthy. Confidence: High.

## Timeline (UTC)
- 09:32 PR #412 merged (`api` 2.7.3 -> 2.8.0); Flux applied it at 09:36.
- 09:38 first OOMKilled; 09:40 CrashLoopBackOff on 3/3 new pods; old ReplicaSet scaled to 1 by the rollout.

## Evidence
```
$ kubectl --context aks-prod-weu-ro -n shop get pods -l app=api
NAME                   READY   STATUS             RESTARTS      AGE
api-7d9f8c6b5-4kq2x    0/1     CrashLoopBackOff   6 (40s ago)   9m
api-7d9f8c6b5-9xw7m    0/1     CrashLoopBackOff   6 (35s ago)   9m
api-5b6c7d8e9-p2r4t    1/1     Running            0             3d
```
```
$ kubectl --context aks-prod-weu-ro -n shop describe pod api-7d9f8c6b5-4kq2x
...
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
    Limits:
      memory:  256Mi
```
```
$ kubectl --context aks-prod-weu-ro -n shop logs api-7d9f8c6b5-4kq2x --previous --tail 20
... loading product catalog cache (48213 items)
```
Meaning: the new version preloads the catalog cache at startup; the container is killed for exceeding its limit, not by the node.
```
$ kubectl --context aks-prod-weu-ro top nodes
NAME                          CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
aks-user-12345678-vmss000000  812m         21%    6120Mi          47%
...
```
Meaning: no node memory pressure.

## Hypotheses
| Hypothesis | Result | Evidence |
|---|---|---|
| Node memory pressure / eviction | Ruled out | `top nodes` < 50%, no `Evicted` events |
| Bad config or missing Secret reference | Ruled out | no `CreateContainerConfigError`; logs reach cache load |
| Memory limit too low for v2.8.0 | Confirmed | `OOMKilled`, exit 137, limit 256Mi, crash during cache preload |

## Root cause
v2.8.0 preloads the catalog cache at startup and needs more than the 256Mi limit. Confidence: High.

## Impact
Only 1 of 3 replicas serves traffic (the old ReplicaSet); checkout latency and error rate up.

## Remediation options
- A (🟡, recommended): revert PR #412 in the GitOps repo so Flux rolls back to 2.7.3. Uses the normal delivery path.
- B (🟡): `kubectl rollout undo` — faster, but Flux will re-apply 2.8.0 at the next sync unless the Kustomization is suspended.

## Follow-ups
- Change item: raise `api` memory request/limit based on load-test data before re-releasing 2.8.0.
- Alert on `OOMKilled` container restarts in `shop`.
