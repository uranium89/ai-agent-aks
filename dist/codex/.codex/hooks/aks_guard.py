#!/usr/bin/env python3
"""aks-guard: keep AI agents read-only against AKS clusters and Azure.

Checks a shell command before an agent runs it and blocks anything that could
change a cluster or a cloud resource, reveal a secret, or switch the default
kubectl context / Azure subscription. Everything else is left to the host
tool's normal permission flow.

Modes:
  aks_guard.py                hook mode: JSON on stdin with tool_input.command
                              (Claude Code and Codex PreToolUse). Exit 2 + stderr
                              blocks; exit 0 with no output leaves the decision
                              to the host.
  aks_guard.py --cursor       Cursor beforeShellExecution: JSON on stdin with
                              "command"; prints {"permission": ...}.
  aks_guard.py --check CMD    print the verdict for CMD; exit 2 if blocked.
                              Used by the OpenCode plugin and by tests.

Standard library only (Python 3.9+). This is a guardrail, not a security
boundary: the real boundary is a read-only identity (see aks-team/ACCESS.md).
"""
import json
import re
import shlex
import sys

HINT = (
    "Agents are read-only against clusters and Azure. Put the command in the "
    "work item's runbook.md for the operator to run instead."
)

# Commands that only wrap another command.
WRAPPERS = {"sudo", "env", "time", "nohup", "nice", "command", "exec", "builtin",
            "timeout", "watch", "xargs", "caffeinate", "stdbuf"}
WRAPPER_VALUE_FLAGS = {"-n", "-I", "-L", "-P", "-d", "-s", "-E", "-u", "-k"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish", "pwsh", "powershell"}

# Tools whose every use is blocked (interactive, or switch the default target).
FORBIDDEN_TOOLS = {
    "kubectx": "kubectx switches the default kubectl context; pass --context instead",
    "kubens": "kubens changes the default namespace of a context; pass -n instead",
    "k9s": "k9s is interactive and can change resources; use kubectl get/describe",
    "kubelogin": "kubelogin rewrites kubeconfig; the operator manages credentials",
}

SENSITIVE_PATH = re.compile(
    r"(\.kube/|\.azure[^/\s]*/|azureProfile\.json|msal_token_cache|accessTokens\.json"
    r"|\.tfstate\b|terraform\.tfstate|\.terraform/terraform\.tfstate)"
)
SENSITIVE_ENV = re.compile(
    r"\$\{?[A-Za-z0-9_]*(SECRET|PASSWORD|PASSWD|TOKEN|ACCESS_KEY|CLIENT_CERT|SAS)[A-Za-z0-9_]*\}?",
    re.I,
)
# Commands treated as safe for Cursor's auto-allow (everything else is "ask").
READ_ONLY_HELPERS = {
    "rg", "grep", "egrep", "cat", "head", "tail", "less", "wc", "sort", "uniq",
    "cut", "tr", "jq", "yq", "ls", "echo", "printf", "column", "true", "date",
    "awk", "sed", "diff", "git", "kubeconform", "kube-linter", "kubescape",
    "trivy", "checkov", "gitleaks", "tflint", "pluto", "kubent", "conftest",
    "kustomize", "stern", "popeye", "nslookup", "dig", "command", "which",
}


# ---------------------------------------------------------------- parsing

def split_segments(command):
    """Split a shell command into simple commands (lists of tokens)."""
    text = command.replace("\\\n", " ").replace("`", "\n")
    segments = []
    for line in text.split("\n"):
        lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|()<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        try:
            tokens = list(lexer)
        except ValueError:  # unbalanced quotes: fall back to a plain split
            tokens = line.split()
        current = []
        for tok in tokens:
            if tok and all(c in ";&|()" for c in tok):
                if current:
                    segments.append(current)
                current = []
            else:
                current.append(tok)
        if current:
            segments.append(current)
    return segments


def basename(tok):
    name = tok.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].lower()
    return name[:-4] if name.endswith(".exe") else name


def strip_wrappers(tokens):
    """Return tokens starting at the real executable."""
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tok):  # VAR=value prefix
            i += 1
            continue
        name = basename(tok)
        if name in WRAPPERS:
            i += 1
            while i < len(tokens) and tokens[i].startswith("-"):
                i += 2 if tokens[i] in WRAPPER_VALUE_FLAGS else 1
            if name == "timeout" and i < len(tokens) and re.match(r"^\d", tokens[i]):
                i += 1
            continue
        break
    return tokens[i:]


def parse_args(args, value_flags):
    """Split args into (positionals, options). options maps flag -> list of values."""
    positionals, options = [], {}
    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "--":
            positionals.extend(args[i + 1:])
            break
        if tok.startswith("--"):
            if "=" in tok:
                name, val = tok.split("=", 1)
            elif tok in value_flags and i + 1 < len(args):
                name, val = tok, args[i + 1]
                i += 1
            else:
                name, val = tok, ""
            options.setdefault(name, []).append(val)
        elif tok.startswith("-") and len(tok) > 1 and not re.match(r"^-\d", tok):
            name = tok[:2]
            if name in value_flags:
                if len(tok) > 2:
                    val = tok[2:].lstrip("=")
                elif i + 1 < len(args):
                    val = args[i + 1]
                    i += 1
                else:
                    val = ""
                options.setdefault(name, []).append(val)
            elif "=" in tok:
                name, val = tok.split("=", 1)
                options.setdefault(name, []).append(val)
            else:
                options.setdefault(tok, []).append("")
        else:
            positionals.append(tok)
        i += 1
    return positionals, options


def has(options, *names):
    return any(n in options for n in names)


def values(options, *names):
    out = []
    for n in names:
        out.extend(options.get(n, []))
    return out


# ---------------------------------------------------------------- kubectl

KUBECTL_VALUE_FLAGS = {
    "--context", "--cluster", "--user", "-n", "--namespace", "--kubeconfig", "-s",
    "--server", "--token", "--as", "--as-group", "--as-uid", "--request-timeout",
    "-v", "--v", "-l", "--selector", "-o", "--output", "-f", "--filename", "-c",
    "--container", "--field-selector", "--sort-by", "--tail", "--since",
    "--since-time", "-L", "--label-columns", "--template", "-k", "--kustomize",
    "--chunk-size", "--raw", "--subresource", "-p", "--patch", "--dry-run",
    "--type", "--for", "--timeout", "--limit-bytes", "--max-log-requests",
    "--certificate-authority", "--tls-server-name", "--revision", "--api-group",
    "--cache-dir", "--profile", "--profile-output", "--field-manager",
}
KUBECTL_READ = {"get", "describe", "logs", "top", "events", "explain", "api-resources",
                "api-versions", "version", "cluster-info", "diff", "kustomize",
                "completion", "auth", "rollout", "config", "help", "plugin", "options"}
KUBECTL_NO_CONTEXT = {"kustomize", "completion", "config", "help", "plugin", "options", "explain"}
SECRET_OUTPUTS_OK = {"", "name", "wide"}


def is_secret_resource(tok):
    for part in tok.lower().split(","):
        kind = part.split("/", 1)[0].split(".", 1)[0]
        if kind in ("secret", "secrets"):
            return True
    return False


def check_kubectl(args):
    pos, opts = parse_args(args, KUBECTL_VALUE_FLAGS)
    if has(opts, "-h", "--help") or not pos:
        return None
    verb = pos[0]
    dry_run = values(opts, "--dry-run")
    if verb not in KUBECTL_READ:
        if dry_run and dry_run[-1] in ("client", "server"):
            return None if has(opts, "--context") or dry_run[-1] == "client" else \
                "kubectl --dry-run=server needs an explicit --context"
        return "kubectl %s changes or touches the cluster" % verb
    if has(opts, "-w", "--watch", "--watch-only") or (verb == "logs" and has(opts, "-f", "--follow")):
        return "watch/follow never exits; use a one-shot get or logs with --tail/--since"
    sub = pos[1] if len(pos) > 1 else ""
    if verb == "auth" and sub not in ("can-i", "whoami", ""):
        return "kubectl auth %s changes RBAC" % sub
    if verb == "rollout" and sub not in ("status", "history"):
        return "kubectl rollout %s changes workloads" % sub
    if verb == "plugin" and sub not in ("list", ""):
        return "kubectl plugin %s is not allowed" % sub
    if verb == "cluster-info" and sub == "dump":
        return "kubectl cluster-info dump is too heavy for a live cluster; query what you need"
    if verb == "config":
        if sub not in ("view", "get-contexts", "current-context", "get-clusters", "get-users"):
            return "kubectl config %s changes kubeconfig; pass --context on each command" % (sub or "")
        if has(opts, "--raw", "--flatten"):
            return "kubectl config view --raw prints credentials"
    if verb == "get":
        raw = " ".join(values(opts, "--raw")).lower()
        if "secret" in raw:
            return "reading Secret objects through --raw is not allowed"
        output = (values(opts, "-o", "--output") or [""])[-1].split("=", 1)[0]
        if any(is_secret_resource(p) for p in pos[1:]) and (
                output not in SECRET_OUTPUTS_OK or has(opts, "--template")):
            return "printing Secret contents is not allowed (use -o name, or describe)"
    if verb == "version" and has(opts, "--client"):
        return None
    if verb not in KUBECTL_NO_CONTEXT and not has(opts, "--context"):
        return ("kubectl needs an explicit target: write `kubectl --context <ctx> %s ...` "
                "(contexts are listed in aks-team/ENVIRONMENT.md)" % verb)
    return None


# ---------------------------------------------------------------- helm

HELM_VALUE_FLAGS = {"--kube-context", "-n", "--namespace", "--kubeconfig", "-f", "--values",
                    "--set", "--set-string", "--set-file", "--set-json", "--version", "-o",
                    "--output", "--repo", "--revision", "--max", "--ca-file", "--cert-file",
                    "--key-file", "--username", "--password", "--registry-config",
                    "--repository-config", "--repository-cache", "--api-versions",
                    "--kube-version", "-s", "--show-only", "--output-dir", "-d", "--destination",
                    "--post-renderer", "--timeout", "-l", "--selector", "--filter"}
HELM_LOCAL = {"lint", "template", "show", "inspect", "search", "version", "env", "dependency",
              "dep", "repo", "verify", "package", "create", "pull", "fetch", "completion", "help"}
HELM_CLUSTER_READ = {"list", "ls", "status", "history", "hist", "get", "diff"}


def check_helm(args):
    pos, opts = parse_args(args, HELM_VALUE_FLAGS)
    if has(opts, "-h", "--help") or not pos:
        return None
    verb, sub = pos[0], (pos[1] if len(pos) > 1 else "")
    if verb in HELM_LOCAL:
        if verb == "repo" and sub == "remove":
            return "helm repo remove changes local config the operator relies on"
        return None
    if verb == "plugin":
        return None if sub == "list" else "helm plugin %s installs or runs code" % sub
    if verb not in HELM_CLUSTER_READ:
        return "helm %s changes the cluster; use helm template / helm diff to preview" % verb
    if verb == "get" and sub not in ("notes", "metadata"):
        return "helm get %s can print secret values; use helm get notes/metadata or helm status" % sub
    if not has(opts, "--kube-context"):
        return "helm needs an explicit target: write `helm --kube-context <ctx> %s ...`" % verb
    return None


# ---------------------------------------------------------------- terraform / tofu / terragrunt

TF_VALUE_FLAGS = {"-chdir", "-var", "-var-file", "-target", "-out", "-state", "-backend-config",
                  "-parallelism", "-lock-timeout", "-replace", "-generate-config-out"}
TF_ALLOWED = {"fmt", "validate", "init", "plan", "show", "providers", "version", "graph",
              "output", "state", "workspace", "get", "modules", "metadata", "help"}


def check_terraform(args, tool):
    pos, opts = parse_args(args, TF_VALUE_FLAGS)
    if has(opts, "-help", "-h", "--help", "-version", "--version") or not pos:
        return None
    if tool == "terragrunt":
        if pos[0] in ("run-all", "run") and len(pos) > 1:
            pos = pos[1:]
        if pos[0] in ("hclfmt", "hcl", "render-json", "graph-dependencies",
                      "output-module-groups", "validate-inputs", "find", "list", "info"):
            return None
    verb, sub = pos[0], (pos[1] if len(pos) > 1 else "")
    if verb not in TF_ALLOWED:
        return "%s %s changes infrastructure or state; only fmt/validate/init/plan are allowed" % (tool, verb)
    if verb == "init" and has(opts, "-migrate-state", "-force-copy"):
        return "%s init -migrate-state moves state" % tool
    if verb == "output" and has(opts, "-json", "-raw"):
        return "%s output -json/-raw prints sensitive outputs" % tool
    if verb == "show" and has(opts, "-json") and len(pos) < 2:
        return "%s show -json of the current state prints secrets; pass a plan file" % tool
    if verb == "state" and sub not in ("list", ""):
        return "%s state %s reads or changes raw state; use state list" % (tool, sub)
    if verb == "workspace" and sub not in ("list", "show", ""):
        return "%s workspace %s changes workspaces" % (tool, sub)
    return None


# ---------------------------------------------------------------- az

AZ_VALUE_FLAGS = {"--method", "-m", "--body", "-b", "--uri", "-u", "--url", "--subscription",
                  "-g", "--resource-group", "-n", "--name", "--query", "-o", "--output",
                  "--analytics-query", "--workspace", "--resource", "--headers"}
AZ_READ_VERBS = {"show", "list", "query", "version", "wait", "summarize", "what-if", "validate",
                 "get-upgrades", "get-versions", "get-os-options", "list-locations",
                 "list-usages", "list-skus", "list-sizes", "list-versions", "list-deleted",
                 "get-instance-view", "find"}
AZ_LOCAL_GROUPS = {("bicep",)}
AZ_SECRETY = re.compile(r"(credential|secret|password|token|sas|connection-string|keys?$|kubeconfig|login)")
AZ_BLOCKED = {
    ("account", "set"): "az account set changes the default subscription; pass --subscription",
    ("aks", "get-credentials"): "az aks get-credentials writes kubeconfig; the operator manages credentials",
    ("aks", "command", "invoke"): "az aks command invoke runs commands inside the cluster",
    ("aks", "check-acr"): "az aks check-acr starts a pod in the cluster",
    ("aks", "browse"): "az aks browse opens a proxy to the cluster",
}


def check_az(args):
    pos = []
    for tok in args:
        if tok.startswith("-"):
            break
        pos.append(tok)
    _, opts = parse_args(args[len(pos):], AZ_VALUE_FLAGS)
    if has(opts, "-h", "--help", "--version") or not pos:
        return None
    for prefix, reason in AZ_BLOCKED.items():
        if tuple(pos[:len(prefix)]) == prefix:
            return reason
    if pos[0] == "bicep":
        ok = len(pos) > 1 and pos[1] in ("build", "lint", "format", "version", "list-versions",
                                          "build-params", "generate-params", "decompile")
        return None if ok else "az bicep %s changes the local toolchain" % " ".join(pos[1:])
    if pos[0] == "rest":
        method = (values(opts, "--method", "-m") or ["get"])[-1].lower()
        if method not in ("get", "head") or has(opts, "--body", "-b"):
            return "az rest is allowed only with --method get"
        return None
    if pos[0] in ("login", "logout"):
        return "az %s changes credentials; the operator signs in" % pos[0]
    if pos[0] == "keyvault" and len(pos) > 2 and pos[1] in ("secret", "certificate") \
            and pos[-1] in ("list", "list-versions", "list-deleted"):
        return None
    if any(AZ_SECRETY.search(p) for p in pos):
        return "az %s can reveal secrets or credentials" % " ".join(pos)
    verb = pos[-1]
    if verb in AZ_READ_VERBS or verb.startswith("show-") or (
            verb.startswith("list-") and not AZ_SECRETY.search(verb)):
        return None
    return "az %s is not a read-only command" % " ".join(pos)


# ---------------------------------------------------------------- flux / argocd / istioctl / velero

FLUX_VALUE_FLAGS = {"--context", "-n", "--namespace", "--kubeconfig", "--path", "--kustomization",
                    "--timeout", "--kind", "--name", "--api-version", "-l", "--label-selector",
                    "--tail", "--since", "--level"}
FLUX_READ = {"get", "logs", "stats", "tree", "trace", "events", "version", "check", "diff",
             "export", "completion", "help", "build", "envsubst"}


def check_flux(args):
    pos, opts = parse_args(args, FLUX_VALUE_FLAGS)
    if has(opts, "-h", "--help") or not pos:
        return None
    verb = pos[0]
    if verb not in FLUX_READ:
        return "flux %s changes the cluster or GitOps state" % verb
    if has(opts, "-f", "--follow", "-w", "--watch"):
        return "watch/follow never exits"
    needs_ctx = verb not in ("completion", "help", "build", "envsubst") and not (
        verb == "version" and has(opts, "--client"))
    if needs_ctx and not has(opts, "--context"):
        return "flux needs an explicit target: write `flux --context <ctx> %s ...`" % verb
    return None


def check_argocd(args):
    pos, opts = parse_args(args, {"--server", "--auth-token", "-o", "--output", "--grpc-web-root-path",
                                  "--revision", "--group", "--kind", "--name", "--namespace",
                                  "--tail", "--since-seconds"})
    if has(opts, "-h", "--help") or not pos:
        return None
    group, sub = pos[0], (pos[1] if len(pos) > 1 else "")
    if group in ("version", "context", "completion", "help"):
        return None
    reads = {"app": {"get", "list", "diff", "history", "manifests", "resources", "logs"},
             "appset": {"get", "list"}, "cluster": {"get", "list"}, "proj": {"get", "list"},
             "repo": {"get", "list"}, "account": {"get-user-info", "list", "can-i"}}
    if sub in reads.get(group, set()):
        return None
    return "argocd %s %s changes Argo CD or the cluster" % (group, sub)


def check_istioctl(args):
    pos, opts = parse_args(args, {"--context", "-n", "--namespace", "-o", "--output", "--revision", "-f"})
    if has(opts, "-h", "--help") or not pos:
        return None
    if pos[0] in ("analyze", "proxy-status", "ps", "proxy-config", "pc", "version", "validate"):
        return None
    if pos[0] in ("x", "experimental") and len(pos) > 1 and pos[1] in ("precheck", "describe"):
        return None
    return "istioctl %s changes the mesh or the cluster" % pos[0]


def check_velero(args):
    pos, opts = parse_args(args, {"--kubecontext", "-n", "--namespace", "-o", "--output", "-l", "--selector"})
    if has(opts, "-h", "--help") or not pos:
        return None
    if pos[0] in ("version", "completion", "help") or (len(pos) > 1 and pos[1] in ("get", "describe", "logs")):
        return None
    return "velero %s changes backups or restores" % " ".join(pos[:2])


CHECKERS = {
    "kubectl": check_kubectl,
    "helm": check_helm,
    "az": check_az,
    "flux": check_flux,
    "argocd": check_argocd,
    "istioctl": check_istioctl,
    "velero": check_velero,
    "terraform": lambda a: check_terraform(a, "terraform"),
    "tofu": lambda a: check_terraform(a, "tofu"),
    "terragrunt": lambda a: check_terraform(a, "terragrunt"),
}


# ---------------------------------------------------------------- verdict

def check_segment(tokens, depth=0):
    """Return (reason or None, executable name) for one simple command."""
    if tokens and basename(tokens[0]) == "watch":
        return "watch never exits; run the command once", "watch"
    first = basename(tokens[0]) if tokens else ""
    tokens = strip_wrappers(tokens)
    if not tokens:
        return ("printing the environment can reveal secrets", "env") if first == "env" else (None, "")
    exe = basename(tokens[0])
    args = tokens[1:]
    if exe in SHELLS or exe == "eval":
        inner = None
        if exe == "eval":
            inner = " ".join(args)
        elif "-c" in args and args.index("-c") + 1 < len(args):
            inner = args[args.index("-c") + 1]
        if inner is not None and depth < 3:
            for seg in split_segments(inner):
                reason, _ = check_segment(seg, depth + 1)
                if reason:
                    return reason, exe
        return None, exe
    if exe in ("find", "fd") and any(t in ("-exec", "-execdir", "-ok", "-x", "-X") for t in args):
        for flag in ("-exec", "-execdir", "-ok", "-x", "-X"):
            if flag in args:
                reason, _ = check_segment(args[args.index(flag) + 1:], depth + 1)
                if reason:
                    return reason, exe
    if exe in FORBIDDEN_TOOLS:
        return FORBIDDEN_TOOLS[exe], exe
    if exe == "printenv" or (exe == "export" and args[:1] == ["-p"]):
        return "printing the environment can reveal secrets", exe
    if exe not in CHECKERS and any(SENSITIVE_PATH.search(t) for t in args):
        return "reading kubeconfig, Azure login files or Terraform state can reveal secrets", exe
    checker = CHECKERS.get(exe)
    if checker:
        return checker(args), exe
    return None, exe


def check_command(command):
    """Return (blocked_reason or None, all_read_only) for a full shell command."""
    if SENSITIVE_ENV.search(command):
        return "referencing secret environment variables is not allowed", False
    read_only = True
    for seg in split_segments(command):
        reason, exe = check_segment(seg)
        if reason:
            return reason, False
        if exe and exe not in CHECKERS and exe not in READ_ONLY_HELPERS:
            read_only = False
    return None, read_only


def message(reason):
    return "BLOCKED by aks-guard: %s. %s" % (reason, HINT)


def main(argv):
    if argv[:1] == ["--check"]:
        reason, _ = check_command(" ".join(argv[1:]))
        print(message(reason) if reason else "allowed")
        return 2 if reason else 0
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    if argv[:1] == ["--cursor"]:
        reason, read_only = check_command(payload.get("command") or "")
        if reason:
            print(json.dumps({"permission": "deny", "user_message": message(reason),
                              "agent_message": message(reason)}))
        else:
            print(json.dumps({"permission": "allow" if read_only else "ask"}))
        return 0
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not command:
        return 0
    reason, _ = check_command(command)
    if reason:
        sys.stderr.write(message(reason) + "\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
