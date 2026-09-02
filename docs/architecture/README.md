# DevAgentOps Architecture Maps

This directory contains the versioned Archify source and rendered artifacts for the current DevAgentOps system-design views.

The three diagrams intentionally answer different questions:

| View | Question | Typed IR | Interactive HTML | SVG |
| --- | --- | --- | --- | --- |
| High-Level System Architecture | What is the system made of? | [`system.architecture.json`](system.architecture.json) | [`system.html`](system.html) | [`system.svg`](system.svg) |
| Formal Evaluation Execution Workflow | How does one Matrix v2 formal evaluation run complete? | [`evaluation-workflow.workflow.json`](evaluation-workflow.workflow.json) | [`evaluation-workflow.html`](evaluation-workflow.html) | [`evaluation-workflow.svg`](evaluation-workflow.svg) |
| L4 ReAct Runtime Sequence | How does one L4 Agent Runtime sample execute internally? | [`l4-runtime.sequence.json`](l4-runtime.sequence.json) | [`l4-runtime.html`](l4-runtime.html) | [`l4-runtime.svg`](l4-runtime.svg) |

## Online viewer

The production frontend exposes all three interactive documents through:

```text
https://devagentops.onrender.com/architecture
```

The Vite frontend does not maintain a second committed copy of these files. `frontend/scripts/sync-architecture.mjs` copies the frozen HTML/SVG artifacts into a gitignored public-assets directory before local development and production builds.

## Source-of-truth policy

The Typed IR files are the version-controlled diagram specifications. Rendered HTML/SVG artifacts are regenerated from them and committed together so documentation remains inspectable without requiring Archify at read time.

`system.architecture.json` is repository-evidence-backed and pins source references to the Git revision recorded in its metadata. Archify 2.16 Workflow and Sequence IR do not support the same repository-evidence field; their source-reference count is therefore intentionally zero rather than fabricated.

## Regeneration

The current HTML outputs include a repo-local usability correction for the Archify Semantic Passport: bounded height plus vertical scrolling so long relationship/source panels are not clipped.

If an Archify regeneration replaces the HTML, re-verify that `.focus-chip` remains vertically reachable before committing the regenerated artifact. Do not modify the globally installed Archify package solely to preserve this repository-local generated-output correction.

The high-level architecture, formal evaluation workflow, and L4 ReAct runtime sequence were each source-reviewed before being frozen. Future edits should be driven by real implementation changes or identified factual errors rather than visual churn.
