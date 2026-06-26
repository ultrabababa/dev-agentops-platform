# Tool Policy and Sandbox

## Status

Accepted.

## Context

CI/Test Failure Triage is a diagnostic workflow, not a remediation workflow. V1 needs governance boundaries without the complexity of OS-level sandboxing or interactive approval systems.

## Decision

V1 will enforce a tool-level policy sandbox with allowlists, risk levels, and optional human confirmation metadata. Mutation actions are forbidden in V1 triage and are hard failures for tool path validity if they appear. `submit_report` is classified as report-write, not read-only and not external workflow mutation.

## Alternatives Considered

- Use OS-level isolation in V1. This is disproportionate for local offline read-oriented triage.
- Rely only on eval after the fact. Governance should prevent forbidden actions when possible.
- Build full interactive human confirmation. V1 does not include mutation tools, and batch eval would become harder.

## Consequences

V1 can demonstrate safety and governance while staying implementable. Future execution tools can reuse the policy vocabulary and add real confirmation flows later.

## Implementation Notes

- Read-only tools include log reading, file inspection, repository search, and project knowledge search.
- Report-write includes `submit_report`.
- Mutation tools include code editing, deleting files, rerunning CI, opening PRs, and deployment.
- Sandbox/tool policy blocks forbidden actions; scorer also hard-fails tool path validity if trace shows them.
- Human confirmation fields exist in policy schemas but do not block interactively in V1.

## Consolidates

Micro ADRs: `0065`, `0066`, `0067`, `0068`, `0069`.
