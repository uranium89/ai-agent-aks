---
description: {{description shared/agents/iac-engineer.md}}
mode: subagent
model: anthropic/claude-sonnet-5-5
temperature: 0.2
permission:
  edit: allow
  webfetch: allow
  bash:
    "*": allow
    "git push*": deny
---

{{body shared/agents/iac-engineer.md}}
