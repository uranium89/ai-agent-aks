// Runs .opencode/hooks/aks_guard.py before every bash command and blocks what it rejects.
// Fails closed: if the guard can't run, the command is blocked.
import { spawnSync } from "node:child_process"
import path from "node:path"

export const AksGuard = async ({ directory, worktree }) => {
  const script = path.join(worktree || directory, ".opencode", "hooks", "aks_guard.py")
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return
      const res = spawnSync("python3", [script, "--check", output.args.command], { encoding: "utf8" })
      if (res.status === 2) throw new Error(res.stdout.trim())
      if (res.status !== 0) throw new Error("aks-guard could not run: " + (res.stderr || res.error))
    },
  }
}
