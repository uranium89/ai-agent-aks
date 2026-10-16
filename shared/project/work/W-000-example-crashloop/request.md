Status: Ready for operator
Type: incident
Severity: SEV2

# W-000: api pods in CrashLoopBackOff on prod after release

_Worked example. Ignore it when planning real work; delete it once the first real item exists._

## Environments
- `aks-prod-weu-ro` (prod), subscription `00000000-0000-0000-0000-000000000000`

## Symptom
Since about 09:40 UTC, `api` in namespace `shop` restarts repeatedly; checkout error rate is up. Release `api` v2.8.0 was merged at 09:32.

## Acceptance Criteria
- [ ] Root cause identified with evidence.
- [ ] Runbook restores all `api` replicas to Ready without touching other workloads.
- [ ] After the operator runs it, all `api` pods are Ready with 0 restarts for 10 minutes.

## Out of scope
- Fixing the memory regression in v2.8.0 itself (follow-up change item).

## Acceptance
- Criterion 1: met, `diagnosis.md` Root cause.
- Criterion 2: met, `runbook.md` reviewed in `review.md` Loop 1 (APPROVED).
- Criterion 3: pending `verify W-000`.
