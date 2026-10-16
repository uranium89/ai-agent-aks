# Read-only Access for the Agents

The agents run commands with whatever identity your shell has. The command guard (`aks-guard`) blocks write commands, but it is a guardrail, not a security boundary. The real boundary is an identity that **cannot** write. Set this up once, before the kickoff. Only you (the operator) run these commands; the agents never do.

## 1. A read-only identity

Use a dedicated Entra ID group, for example `aks-agents-readonly`, with yourself (or a dedicated user or service principal) as a member. Assign these Azure roles:

| Role | Scope | Why |
|---|---|---|
| `Reader` | each AKS resource group, the node resource group (`MC_...`), and the network / ACR / Key Vault resource groups | `az aks show`, node pools, VNets, NSGs, load balancers |
| `Azure Kubernetes Service Cluster User Role` | each AKS cluster | download a non-admin kubeconfig |
| `Azure Kubernetes Service RBAC Reader` | each AKS cluster (clusters with Azure RBAC for Kubernetes) | read most objects; cannot read Secrets |
| `Monitoring Reader` and `Log Analytics Reader` | the Log Analytics workspace(s) and clusters | Container Insights, metrics, activity log |

```sh
GROUP_ID=$(az ad group show --group aks-agents-readonly --query id -o tsv)
AKS_ID=$(az aks show -g <rg> -n <cluster> --subscription <sub> --query id -o tsv)
az role assignment create --assignee-object-id $GROUP_ID --assignee-principal-type Group --role "Reader" --scope /subscriptions/<sub>/resourceGroups/<rg>
az role assignment create --assignee-object-id $GROUP_ID --assignee-principal-type Group --role "Azure Kubernetes Service Cluster User Role" --scope $AKS_ID
az role assignment create --assignee-object-id $GROUP_ID --assignee-principal-type Group --role "Azure Kubernetes Service RBAC Reader" --scope $AKS_ID
```

Do **not** give the group `Contributor`, `Azure Kubernetes Service Cluster Admin Role`, `Azure Kubernetes Service RBAC Writer/Admin/Cluster Admin`, or `Key Vault Secrets User`.

## 2. Cluster-scoped reads (Kubernetes RBAC)

`RBAC Reader` and the built-in `view` ClusterRole don't cover cluster-scoped objects such as nodes. Apply this ClusterRole once per cluster. Clusters that use Kubernetes RBAC with Entra ID (not Azure RBAC) also need the `view` binding at the bottom.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: aks-agent-readonly-cluster
rules:
  - apiGroups: [""]
    resources: [nodes, namespaces, persistentvolumes, componentstatuses]
    verbs: [get, list]
  - apiGroups: ["storage.k8s.io", "scheduling.k8s.io", "networking.k8s.io", "node.k8s.io",
                "apiextensions.k8s.io", "apiregistration.k8s.io", "admissionregistration.k8s.io",
                "policy", "metrics.k8s.io", "rbac.authorization.k8s.io", "events.k8s.io",
                "discovery.k8s.io", "gateway.networking.k8s.io"]
    resources: ["*"]
    verbs: [get, list]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: aks-agent-readonly-cluster
roleRef: {apiGroup: rbac.authorization.k8s.io, kind: ClusterRole, name: aks-agent-readonly-cluster}
subjects:
  - {apiGroup: rbac.authorization.k8s.io, kind: Group, name: "<GROUP_OBJECT_ID>"}
---
# Only for clusters using Kubernetes RBAC (not Azure RBAC). `view` excludes Secrets.
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: aks-agent-view
roleRef: {apiGroup: rbac.authorization.k8s.io, kind: ClusterRole, name: view}
subjects:
  - {apiGroup: rbac.authorization.k8s.io, kind: Group, name: "<GROUP_OBJECT_ID>"}
```

## 3. A separate shell profile for the agents

Keep the agents' Azure login and kubeconfig apart from your own admin ones, so a session can't use your write access even by mistake:

```sh
export AZURE_CONFIG_DIR="$HOME/.azure-aks-agent"
export KUBECONFIG="$HOME/.kube/aks-agent.config"
az login                       # sign in as the read-only identity
az aks get-credentials -g <rg> -n <cluster> --subscription <sub> \
  --file "$KUBECONFIG" --context <cluster>-ro   # never --admin
kubelogin convert-kubeconfig -l azurecli --kubeconfig "$KUBECONFIG"
```

Start your AI tool from this shell (for example with an alias `aks-agent='AZURE_CONFIG_DIR=... KUBECONFIG=... claude'`). Record the context names (`<cluster>-ro`) in `aks-team/ENVIRONMENT.md`.

## 4. Check it

Each of these must answer `no`:

```sh
kubectl --context <cluster>-ro auth can-i delete pods -A
kubectl --context <cluster>-ro auth can-i get secrets -A
kubectl --context <cluster>-ro auth can-i patch deployments -A
```

And these must answer `yes`: `auth can-i list pods -A`, `auth can-i list nodes`.

If your clusters have local accounts enabled, the agents can still be stopped from using them by never giving them an admin kubeconfig; consider disabling local accounts (`--disable-local-accounts`) as a separate, 🔴 change.
