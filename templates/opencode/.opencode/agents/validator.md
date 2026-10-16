---
description: {{description shared/agents/validator.md}}
mode: subagent
model: anthropic/claude-sonnet-5-5
temperature: 0.2
permission:
  edit: allow
  webfetch: deny
  bash:
    "*": allow
    "git push*": deny
---

{{body shared/agents/validator.md}}
