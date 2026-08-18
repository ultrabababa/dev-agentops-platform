# Tool Policy and Sandbox

## Status

Accepted.

## Context

CI/Test Failure Triage is a diagnostic workflow, not a remediation workflow. V1 needs governance boundaries without the complexity of OS-level sandboxing or interactive approval systems.

## Decision

V1 will enforce a tool-level policy sandbox for executable tool actions. Mutation actions are forbidden in V1 triage and are hard failures for tool path validity if they appear.

The earlier policy vocabulary distinguished `submit_report` as a report-write action so report production would not be confused with read-only inspection or external workflow mutation. ADR 0128 refines the concrete L4 protocol: L4 V1 does **not** expose `submit_report` as a provider-native tool. Report submission is a semantic terminal Runtime action produced when an AssistantMessage contains no ToolCalls and its visible text is interpreted as the final Structured Triage Report candidate.

Therefore the L4 executable Tool Registry contains only read-only investigation tools. The report-write classification remains useful as a governance concept for future runtimes or APIs that represent report persistence as an explicit action, but it must not be read as requiring a `submit_report` ToolCall in L4.

## Alternatives Considered

- Use OS-level isolation in V1. This is disproportionate for local offline read-oriented triage.
- Rely only on eval after the fact. Governance should prevent forbidden actions when possible.
- Build full interactive human confirmation. V1 does not include mutation tools, and batch eval would become harder.

## Consequences

V1 can demonstrate safety and governance while staying implementable. Future execution tools can reuse the policy vocabulary and add real confirmation flows later.

## Implementation Notes

- L4 V1 read-only tools are `read`, `grep`, `find`, and `ls` as frozen by ADR 0128.
- Tool availability is defined by the frozen Tool Registry; L4 Tool Policy governs cross-call execution semantics rather than duplicating a second per-tool allowlist.
- L4 baseline Tool Policy is `single + sequential`; multiple ToolCalls in one Model Decision are rejected as Agent-visible policy errors without executing any of them.
- Final report submission is a terminal Runtime action, not an L4 native tool.
- Mutation tools include code editing, deleting files, rerunning CI, opening PRs, and deployment, and remain forbidden in V1.
- Human confirmation metadata remains future-facing; L4 V1 has no interactive approval flow.

## Consolidates

Micro ADRs: `0065`, `0066`, `0067`, `0068`, `0069`.

## Refined By

[ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md).
