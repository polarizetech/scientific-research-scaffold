## Agents and coordination

Maintained by scientific-research-scaffold (`scaffold update` keeps this section current; edits here are
replaced). The full rules are the [coordination protocol](https://github.com/polarizetech/scientific-research-scaffold/blob/{{scaffold_ref}}/agents/COORDINATION.md).

This repo has specialist roles, each briefed in a file under `.claude/agents/`. Claude Code delegates to
them as subagents. **Other assistants (Codex and the rest): before a task of one of these kinds, read
that file and follow it as your brief.**

{{agent_roster}}

- **Hand back briefly.** Each piece of work ends with a handoff of at most 150 words: Done, Files, Open,
  Next. Pass handoffs between roles, not transcripts.
- **The science gate.** A scientific feature goes researcher, then the person's decision, then engineer.
  Nothing skips the person's decision.
- **Parallel only when independent**: different files, at most three at a time, each in its own worktree.
- **Start cheap, escalate on a signal**: two failed attempts, a design decision across many files, or
  subtle scientific or statistical judgment. Escalate the task, not the session.
- **Codex:** {{codex_routing}}
