# DevAgentOps Agent Notes

## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues for `ultrabababa/dev-agentops-platform`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default five-label triage vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repo with one root `CONTEXT.md` and root `docs/adr/`. See `docs/agents/domain.md`.

## Learning collaboration

When the user is learning:

- Teach primarily through short conversational prompts, not generated HTML or web pages.
- Let the user think and write tests or implementation first; write complete functionality only when explicitly asked.
- Advance in small loops: explain failures, then provide graduated hints.
- Do not populate personal learning reflections in repository issue notes unless explicitly asked.

## Issue learning notes

`docs/issues-notes/` is non-authoritative personal learning and review material. Do not use it as an implementation requirements source.

AI agents may proactively edit issue notes only for factual association work, such as adding or correcting the related GitHub issue, parent PRD, PRD user stories, implementation decisions, ADRs, and glossary terms, following the structure in `docs/issues-notes/ISSUE_NOTE_TEMPLATE.md`.

AI agents must not proactively fill sections that are meant for the user's own understanding or reflection, including "What This Issue Is Really About", "ADRs In My Own Words", diagrams, trade-off reflections, TDD plans, implementation notes, or post-implementation review. Fill those sections only when the user explicitly asks for that specific help.

When implementing or triaging issues, use these sources of truth instead:

- GitHub issue body and acceptance criteria.
- Parent PRD in `docs/prd/`.
- Active ADRs in `docs/adr/`.
- Domain glossary in `CONTEXT.md`.
- Agent guidance in `AGENTS.md` and `docs/agents/`.
- Existing code and tests.

If an issue note conflicts with any source of truth, ignore the issue note. If a note contains a decision that should affect implementation, promote that decision into a GitHub issue, PRD update, or ADR update before relying on it.

## Subagent delegation

Use subagents selectively when a task contains a clear, independently verifiable subtask and delegation will reduce latency or keep noisy exploration out of the main context. The main agent may delegate such work without waiting for the user to request it explicitly.

Good delegation candidates include:

- A specific read-only codebase question, such as tracing one execution path or locating all callers of a symbol. Prefer an `explorer` agent for this work.
- A bounded, repeatable task with an observable deliverable, such as running a focused test set, checking fixtures, summarizing logs, or making a small mechanical change. Prefer `luna_worker` for this work.
- Two or more genuinely independent investigations that can run in parallel without examining or editing the same concern.

Keep the following work in the main agent:

- Clarifying user intent and deciding scope, architecture, domain semantics, or whether an ADR must be reopened.
- Integrating results, reviewing every subagent change, resolving contradictions, and giving the final answer.
- Small tasks where delegation overhead is comparable to doing the work directly.
- Work that depends on rapid back-and-forth across shared state or would require multiple agents to edit the same files.
- Sections of `docs/issues-notes/` reserved for the user's own understanding or reflection.

When delegating:

- Give each subagent one concrete objective, an explicit read-only or file-ownership boundary, the relevant source-of-truth files, the expected output, and the verification to perform.
- Tell writing agents that they share the worktree, must preserve existing and concurrent edits, and must not modify files outside their assigned ownership.
- Prefer read-only delegation. Never assign overlapping write ownership; use only one writer for a file or tightly coupled module at a time.
- Do not ask multiple agents to repeat the same exploration. Normally use one subagent, or at most two in parallel when the investigations are independent.
- Require concise evidence: relevant paths and symbols, commands or tests run, results, and caveats. Treat a subagent report as input, not as proof; the main agent must inspect the resulting diff and verify important claims before accepting it.
- For UI bugs, establish the actual service URL and reproduce the problem before assigning a fixer. Browser reproduction and read-only code mapping may run independently, but only one agent should implement the fix after evidence identifies the failing path.
- Do not delegate merely to reduce use of the main model. Subagents have their own context and tool costs, so use them only when the task structure justifies the coordination overhead.
