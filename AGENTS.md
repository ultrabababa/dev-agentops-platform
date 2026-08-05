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
