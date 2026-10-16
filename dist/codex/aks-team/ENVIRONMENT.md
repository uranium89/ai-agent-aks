# Environment

Shared memory for every agent. Read it before acting. The ops-lead owns Guardrails and Environments; the sre owns Tooling and Inventory.

## Guardrails
_Filled by the ops-lead from the kickoff interview. Mark anything not answered as `UNKNOWN`._
- Report language:
- How changes reach clusters (IaC tool, pipelines, GitOps, Helm):
- Maintenance windows:
- Change approval process:
- SLOs / critical workloads:
- Compliance requirements:
- Monthly budget for the platform:
- Never touch:
- Read-only access set up per `aks-team/ACCESS.md`: yes / no / partly

## Environments
_Only these targets may be used. One row per cluster. `Prod` = yes means extra care (see Hard Limits)._

| Name | Prod | Kube context | Subscription ID | Resource group | Cluster | Region | Notes |
|---|---|---|---|---|---|---|---|
| | | | | | | | _Filled at kickoff._ |

## Tooling
_Filled by the sre: tool, version, or MISSING._

## Inventory
_Filled by the sre during discovery, per environment, with the commands used: Kubernetes version and available upgrades, upgrade channel and maintenance configuration, node pools (VM size, count, autoscaler, OS SKU, zones, max surge), network profile (plugin, mode, policy, outbound type, private cluster, authorized IPs), identity (Entra ID, Azure RBAC, local accounts, Workload Identity, OIDC issuer), add-ons and extensions, namespaces and workload summary._
