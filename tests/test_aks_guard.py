"""Tests for shared/hooks/aks_guard.py. Run: python3 -m unittest discover -s tests"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUARD = ROOT / "shared" / "hooks" / "aks_guard.py"
sys.path.insert(0, str(GUARD.parent))
import aks_guard  # noqa: E402

ALLOWED = [
    "kubectl --context dev get pods -A -o wide",
    "kubectl --context prod -n kube-system logs coredns-abc --tail 200 --since 1h",
    "kubectl --context prod describe node aks-sys-123",
    "kubectl --context prod get events -A --sort-by=.lastTimestamp",
    "kubectl --context prod top nodes",
    "kubectl --context prod get secrets -n app",
    "kubectl --context prod get secret db -o name",
    "kubectl --context prod describe secret db",
    "kubectl --context prod auth can-i --list",
    "kubectl --context prod rollout history deploy/api",
    "kubectl --context prod diff -f k8s/",
    "kubectl --context prod apply -f x.yaml --dry-run=server",
    "kubectl apply -f x.yaml --dry-run=client -o yaml",
    "kubectl config get-contexts",
    "kubectl version --client",
    "kubectl kustomize overlays/prod | kubeconform -strict -summary",
    "helm template api ./charts/api -f values-prod.yaml",
    "helm lint ./charts/api",
    "helm --kube-context prod list -A",
    "helm --kube-context prod history api -n app",
    "helm --kube-context prod get notes api",
    "terraform fmt -check -recursive",
    "terraform -chdir=infra validate",
    "terraform init -backend=false",
    "terraform plan -lock=false -out tfplan",
    "terraform show -json tfplan",
    "terraform state list",
    "terragrunt run-all plan",
    "tofu validate",
    "az aks show -g rg -n c --subscription s -o json",
    "az aks get-upgrades -g rg -n c",
    "az aks nodepool list -g rg --cluster-name c",
    "az monitor log-analytics query -w id --analytics-query 'KubePodInventory | take 5'",
    "az graph query -q \"Resources | where type =~ 'microsoft.containerservice/managedclusters'\"",
    "az deployment group what-if -g rg -f main.bicep",
    "az bicep build --file main.bicep",
    "az keyvault secret list --vault-name v",
    "az rest --url https://management.azure.com/subscriptions/x",
    "az advisor recommendation list --category Cost",
    "flux --context dev get kustomizations -A",
    "argocd app diff api",
    "istioctl analyze --context dev -A",
    "velero backup get",
    "rg -n 'kubectl delete' docs",
    "kubescape scan framework nsa k8s/",
    "trivy config infra/",
    "cat envs/prod.tfvars",
]

BLOCKED = [
    "kubectl get pods",
    "kubectl --context prod delete pod x",
    "kubectl --context prod scale deploy/api --replicas 0",
    "kubectl --context prod rollout restart deploy/api",
    "kubectl --context prod drain aks-node-1",
    "kubectl --context prod cordon aks-node-1",
    "kubectl --context prod exec -it x -- sh",
    "kubectl --context prod debug node/x -it --image busybox",
    "kubectl --context prod port-forward svc/x 8080:80",
    "kubectl --context prod logs -f x",
    "kubectl --context prod get pods -w",
    "kubectl --context prod get secret db -o yaml",
    "kubectl --context prod get secret,cm -ojsonpath={.data}",
    "kubectl --context prod get secrets/db --template={{.data}}",
    "kubectl --context prod get --raw /api/v1/namespaces/x/secrets",
    "kubectl config use-context prod",
    "kubectl config view --raw",
    "kubectl --context prod apply -f x.yaml",
    "kubectl apply -f x.yaml --dry-run=server",
    "kubectl --context dev get pods && kubectl --context dev delete ns foo",
    "kubectl --context dev get pods; kubectl --context dev delete ns foo",
    "kubectl --context dev get pods\nkubectl --context dev delete ns foo",
    "bash -c \"kubectl --context dev scale deploy x --replicas 0\"",
    "sh -c 'helm --kube-context dev uninstall api'",
    "echo x | xargs -I{} kubectl --context dev delete pod {}",
    "find . -name '*.yaml' -exec kubectl --context dev apply -f {} \\;",
    "sudo /usr/local/bin/kubectl --context dev delete ns x",
    "watch kubectl --context dev get pods",
    "helm --kube-context dev upgrade api ./chart",
    "helm --kube-context dev rollback api 3",
    "helm --kube-context dev get values api",
    "helm --kube-context dev get manifest api",
    "helm list -A",
    "terraform apply -auto-approve",
    "terraform -chdir=infra destroy",
    "terraform import azurerm_resource_group.x /subscriptions/x",
    "terraform output -json",
    "terraform show -json",
    "terraform state rm x",
    "terraform state pull",
    "terragrunt run-all apply",
    "az aks upgrade -g rg -n c -k 1.31",
    "az aks nodepool scale -g rg --cluster-name c -n np -c 5",
    "az aks stop -g rg -n c",
    "az aks get-credentials -g rg -n c --admin",
    "az aks command invoke -g rg -n c --command 'kubectl get pods'",
    "az aks check-acr -g rg -n c --acr x",
    "az account set -s x",
    "az account get-access-token",
    "az keyvault secret show --vault-name v -n s",
    "az storage account keys list -n x",
    "az acr credential show -n x",
    "az rest --method post --url x",
    "az group delete -n rg --yes",
    "az login",
    "flux --context dev reconcile ks x",
    "flux --context dev suspend hr api",
    "flux get ks",
    "argocd app sync api",
    "istioctl install -y",
    "velero restore create --from-backup x",
    "kubectx prod",
    "k9s",
    "cat ~/.kube/config",
    "cat infra/terraform.tfstate",
    "head ~/.kube/cache/kubelogin/token.json",
    "echo $ARM_CLIENT_SECRET",
    "printenv",
    "env",
]


class GuardTest(unittest.TestCase):
    def test_allowed(self):
        for cmd in ALLOWED:
            with self.subTest(cmd=cmd):
                reason, _ = aks_guard.check_command(cmd)
                self.assertIsNone(reason)

    def test_blocked(self):
        for cmd in BLOCKED:
            with self.subTest(cmd=cmd):
                reason, _ = aks_guard.check_command(cmd)
                self.assertIsNotNone(reason)

    def run_guard(self, args, payload):
        return subprocess.run([sys.executable, str(GUARD)] + args, input=json.dumps(payload),
                              capture_output=True, text=True)

    def test_hook_mode_blocks_with_exit_2(self):
        res = self.run_guard([], {"tool_input": {"command": "kubectl --context p delete ns x"}})
        self.assertEqual(res.returncode, 2)
        self.assertIn("BLOCKED by aks-guard", res.stderr)

    def test_hook_mode_allows_silently(self):
        res = self.run_guard([], {"tool_input": {"command": "kubectl --context p get ns"}})
        self.assertEqual((res.returncode, res.stdout), (0, ""))

    def test_cursor_mode(self):
        deny = json.loads(self.run_guard(["--cursor"], {"command": "kubectl --context p delete ns x"}).stdout)
        allow = json.loads(self.run_guard(["--cursor"], {"command": "kubectl --context p get ns | rg app"}).stdout)
        ask = json.loads(self.run_guard(["--cursor"], {"command": "npm install"}).stdout)
        self.assertEqual([deny["permission"], allow["permission"], ask["permission"]], ["deny", "allow", "ask"])


if __name__ == "__main__":
    unittest.main()
