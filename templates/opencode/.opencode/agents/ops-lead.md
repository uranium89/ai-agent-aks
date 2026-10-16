---
description: {{description shared/agents/ops-lead.md}}
mode: subagent
model: anthropic/claude-opus-5-5
temperature: 0.1
permission:
  edit: allow
  webfetch: deny
  bash:
    "*": deny
    "rg *": allow
    "ls*": allow
    "cat *": allow
    "git status*": allow
    "git diff*": allow
    "git log*": allow
    "command -v *": allow
    "git push*": deny
---

{{body shared/agents/ops-lead.md}}
