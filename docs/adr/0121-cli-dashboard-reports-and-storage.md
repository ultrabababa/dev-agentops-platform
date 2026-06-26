# CLI, Dashboard, Reports, and Storage

## Status

Accepted.

## Context

Formal evaluation should be repeatable and scriptable. The dashboard is still valuable for trace review, leaderboard inspection, and badcase review, but it should not become the job orchestration layer in V1.

## Decision

V1 formal evaluation is driven by CLI commands. The dashboard is read-and-review focused. Evaluation results are stored in SQLite for API/dashboard access and emitted to ignored filesystem artifacts for review and demos. Exporting milestone reports into versioned docs is optional.

## Alternatives Considered

- Trigger formal and debug runs from the dashboard. This requires job orchestration, cancellation, progress state, error recovery, concurrency handling, and credential management.
- Commit every eval output. This would make git noisy and mix transient run artifacts with source decisions.
- Store only files or only database rows. The dashboard needs queryable data, while review and demos benefit from report artifacts.

## Consequences

V1 stays easy to run locally and easy to inspect. Generated outputs do not pollute the repository unless deliberately exported as milestones.

## Implementation Notes

- Required CLI commands include eval doctor, eval run, debug run, component freeze, and optional report export.
- Formal eval runner always runs eval doctor first.
- SQLite stores runs, manifests, trace events, reports, eval results, badcases, and leaderboard rows.
- Artifacts directory stores report markdown, report JSON, leaderboard JSON, and badcase JSON and should be ignored by git.
- Dashboard views include traces, reports, leaderboards, badcases, and badcase review.

## Consolidates

Micro ADRs: `0088`, `0089`, `0091`, `0092`, `0093`, `0094`, `0095`.
