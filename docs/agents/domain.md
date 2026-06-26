# Domain Docs

This is a single-context repo.

## Before exploring, read these

- `CONTEXT.md` at the repo root for the DevAgentOps glossary.
- `docs/adr/README.md` for the active ADR reading order.
- Relevant active ADRs in `docs/adr/` for the area being changed.

Archived micro decisions live in `docs/adr/archive/micro-decisions/`. Read them only when the active consolidated ADRs do not provide enough detail.

## Layout

```text
/
├── CONTEXT.md
├── docs/
│   ├── adr/
│   └── agents/
└── README.md
```

## Use the glossary vocabulary

When naming a domain concept in an issue, PRD, implementation plan, test, or code comment, use the term as defined in `CONTEXT.md`. Avoid synonyms listed under `_Avoid_`.

## Respect ADRs

If a proposed change contradicts an active ADR, call out the contradiction explicitly and explain whether the ADR should be reopened.
