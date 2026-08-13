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
- Keep personal issue learning notes local; do not stage, commit, or publish them.

## Local issue learning notes

`docs/issues-notes/` is an ignored, local-only area for the user's personal learning and review material. Do not treat it as an implementation requirements source, and never stage, commit, or publish its contents.

AI agents must not proactively create or edit local issue notes. Help with a local note only when the user explicitly requests that specific note or section, and preserve sections intended for the user's own understanding or reflection.

When implementing or triaging issues, use these sources of truth instead:

- GitHub issue body and acceptance criteria.
- Parent PRD in `docs/prd/`.
- Active ADRs in `docs/adr/`.
- Domain glossary in `CONTEXT.md`.
- Agent guidance in `AGENTS.md` and `docs/agents/`.
- Existing code and tests.

If a local note conflicts with any source of truth, ignore the note. If it contains a decision that should affect implementation, promote that decision into a GitHub issue, PRD update, or ADR update before relying on it.

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
- Local personal notes under `docs/issues-notes/`; keep this work in the main agent and edit it only when explicitly requested.

When delegating:

- Give each subagent one concrete objective, an explicit read-only or file-ownership boundary, the relevant source-of-truth files, the expected output, and the verification to perform.
- Tell writing agents that they share the worktree, must preserve existing and concurrent edits, and must not modify files outside their assigned ownership.
- Prefer read-only delegation. Never assign overlapping write ownership; use only one writer for a file or tightly coupled module at a time.
- Do not ask multiple agents to repeat the same exploration. Normally use one subagent, or at most two in parallel when the investigations are independent.
- Require concise evidence: relevant paths and symbols, commands or tests run, results, and caveats. Treat a subagent report as input, not as proof; the main agent must inspect the resulting diff and verify important claims before accepting it.
- For UI bugs, establish the actual service URL and reproduce the problem before assigning a fixer. Browser reproduction and read-only code mapping may run independently, but only one agent should implement the fix after evidence identifies the failing path.
- Do not delegate merely to reduce use of the main model. Subagents have their own context and tool costs, so use them only when the task structure justifies the coordination overhead.

## Issue worktree workflow

Use one dedicated Git worktree per implementation Issue.

- Keep the primary repository checkout on `main`. Do not implement Issues directly in the primary checkout.
- Before starting a new Issue, update the primary `main` checkout with `git fetch origin` and a fast-forward-only pull.
- Create a dedicated branch and worktree from the current `main`. Prefer a worktree directory named `issue-<number>-<slug>`.
- Keep one primary branch and one primary worktree per Issue unless there is a concrete reason to split the work.
- Treat the worktree as the ownership boundary for the Issue. Before editing, verify the current worktree path, branch, and working-tree status.
- If the current checkout is `main` or belongs to another Issue, stop and switch to or create the correct Issue worktree before making changes.
- Run Claude Code, Codex, or other implementation agents from the Issue worktree, not from the primary `main` checkout.
- Do not modify another active Issue's worktree.
- Before removing any worktree, inspect `git status --short`. Never discard tracked, staged, or untracked files without first determining whether they are still needed.
- After the PR is merged, update `main`, verify the Issue worktree is clean, remove the worktree, prune worktree metadata, and delete the obsolete local and remote Issue branches.
- If normal branch deletion reports that a branch is not fully merged, do not immediately force-delete it. Verify the PR state and commit ancestry first.
- Use `/private/tmp` worktrees only for disposable review, reproduction, or experimental work. Use the persistent `dev-agentops-worktrees/` directory for normal Issue implementation.
