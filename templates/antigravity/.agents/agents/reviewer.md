---
name: reviewer
description: {{description shared/agents/reviewer.md}}
tools: [view_file, grep_search, replace_file_content, run_command]
mainAgent: false
subagent: true
model: pro
commandExecutionPolicy: sandbox
---

# System Prompt

{{body shared/agents/reviewer.md}}
