# Architecture

Shared memory for every agent. Read it before acting. The aks-architect owns this file, except Quality Gates (secops).

## Current State
_Per environment, summarized from the Inventory in `aks-team/ENVIRONMENT.md`. Link ADRs for significant existing decisions._

## Target Principles
_Networking, identity and access, ingress, secrets, image supply chain, policy, observability, upgrade strategy, multi-tenancy, cost. Link the ADR for each._

## Repo Layout
_Where Terraform/Bicep, manifests, Helm charts, Kustomize overlays, GitOps config, policies and pipelines live. Workflow documents stay in `aks-team/`._

## Delivery Path
_How a change reaches each environment: PR -> pipeline (plan/what-if, manual approval, apply) or GitOps (merge -> Flux/Argo CD sync)._

## Conventions
_Naming, tags, labels, resource requests/limits, probes, PDBs, security context, image registry and pinning, provider/module/chart version pinning._

## Commands
- IaC format / lint / validate:
- IaC preview (read-only):
- Manifests render / validate:
- Manifests preview (read-only):
- Deprecated APIs:
- Policy tests:

## Quality Gates
_Filled by secops: the exact command for each scanner, and whether it runs in CI._
- IaC misconfiguration:
- Kubernetes manifests:
- Secrets:
- Policy as code:
- Live posture (audits):
