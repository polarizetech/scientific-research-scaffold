<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Coordinating agents

How the specialist agents in a repo work together, in parallel where that helps, without spending tokens
on each other. It applies to Claude Code and to Codex; where they differ, it says so.

## What costs tokens

Almost all of an agent session's cost is **context**: every turn resends the conversation so far, and
prompt caching reprices the resend but does not remove it. Measured on one organisation's week of
Claude Code use, cache writes and reads were 90% of the API-equivalent cost and output was 10%.
So the rules below mostly keep contexts small:

- an agent gets the task and a short handoff, never another agent's transcript;
- a session does one task, then ends (or is cleared);
- reading-heavy work goes to a cheap agent that returns a summary;
- parallel agents each build their own context, so more of them costs more, even when they finish sooner.

`scaffold usage` shows what a repo actually used, per model, so these rules can be checked against the
numbers rather than assumed.

## Who does what

One **lead** (the session the person talks to) plans, delegates and integrates. It keeps general work
(planning, small edits, git) and hands everything else to a specialist in `.claude/agents/`:

| agent | takes |
|---|---|
| `scout` | finding and summarising: where something is, what a file or folder does, what changed |
| `computational-engineer` | simulators, models, numerical code, pipelines, tool internals |
| `mathematician` | equations, constants, units, valid ranges; specifies calculators and their reference values |
| `designer` | layout and visual design on the design system |
| `frontend-developer` | building interfaces from the designer's mockups |
| `researcher` | literature and evidence, evidence tiers |
| `analyst` | data analysis and statistics |
| `science-writer` | papers and blog posts |

## Handoffs: how agents talk

Agents talk through the lead, in handoffs. Every agent ends with one, **at most 150 words**:

```
Done: what was done, in one or two lines.
Files: the files created or changed.
Open: questions only the person can answer, and anything left undone.
Next: which agent should go next, and what it needs to know.
```

The lead passes on the handoff, not the transcript. When an agent needs something from another, it
says so under **Next**, and the lead routes it. A handoff is the whole message: if it doesn't fit in 150
words, the task was too big for one agent.

## Order, and the science gate

Some work has to happen in sequence:

- **A scientific feature:** `researcher` (what is known, and its tier), then **the person's decision**,
  then `computational-engineer`. Where the preregistration kit's `tool-scope` module is installed, its
  protocol governs this step.
- **An interface:** `designer` (a mockup on the design system), then `frontend-developer`.
- **A result:** `analyst` (numbers, with their uncertainty), then `science-writer`.

No amount of parallelism skips the person's decision on a scientific feature.

## Parallel work

Run agents in parallel only when their tasks are **independent**: different files, no answer from one
that the other needs.

- At most **three** at a time.
- Each writes in its own worktree (`isolation: worktree`) when more than one of them edits files.
- The lead merges, runs `make check`, and resolves conflicts itself.
- Good fits: the engineer builds while the designer mocks up; the researcher checks several claims at
  once; the scout surveys several folders.

**Agents that message each other directly** (Claude Code's experimental agent teams) cost several times
as much, because each teammate is a full session. Use them only when two agents must iterate back and
forth faster than handoffs allow, such as a designer and a frontend developer converging on one
screen, and end the team when that's done.

## Choosing the model

There is no automatic per-task router in Claude Code or Codex, so the lead follows a rule: **start
cheap, escalate on a signal.**

**Claude Code.** Each agent's frontmatter sets its starting `model` and `effort`, chosen by the profile
(defaults in [`README.md`](README.md)). The lead keeps its own model (the most capable one, at medium
effort). It escalates by re-running a task with a stronger model when:

- tests or checks fail twice on the same task;
- the change is a design decision spanning many files or modules;
- the answer rests on subtle scientific or statistical judgment;
- the agent says it is unsure, or its handoff contradicts the evidence.

Escalate one task, not the session. Changing model mid-conversation discards the prompt cache, which
is model-specific, so escalate by delegating the task afresh rather than switching models partway.

**Codex.** Codex reads `AGENTS.md`, where the scaffold keeps a section pointing at the same agent files
as role briefs. Route with reasoning effort: low for the scout's kind of work, medium by default, high or
xhigh on the same escalation signals. The profile names the default model, and an escalation model if
there is one.

**Local models** (Ollama). Neither Claude Code nor Codex's own agents should be expected to run well on a
small local model, and on a 16 GB laptop the measured sweet spot is around 4 billion parameters: good
for routing, embeddings and answering from retrieved text, not for writing code. Use local models inside
the project's own tools for narrow jobs, and for anything confidential that may not leave the machine.
Their cost is memory and speed, not money.

## Keeping sessions cheap

- One task per session; clear or end it when the task is done.
- Keep `CLAUDE.md` and `AGENTS.md` short: they are resent on every turn.
- Ask the scout to read large files and return what matters, instead of reading them in the lead.
- Prefer lower effort on the capable model to a cascade of models, and measure before tightening further.
- Check `scaffold usage` weekly: on a subscription, the limit is the plan's usage window, and the
  heaviest project is usually one long-running session.
