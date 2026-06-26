# Metrics, Quality Gate, and Leaderboard

## Status

Accepted.

## Context

V1 evaluation needs useful comparison without pretending that one unvalidated composite score can summarize correctness, evidence quality, report completeness, tool path behavior, cost, and stability.

## Decision

V1 will report metric vectors instead of a single composite score. Quality metrics and operational metrics are separate. Leaderboards are partitioned by evaluation method, suite, and model configuration, and use metric-specific rankings. Quality gates are formal evaluation qualification statuses, not eval job success or failure.

## Alternatives Considered

- Collapse all metrics into one weighted score. V1 has no defensible weights yet.
- Let cheap or fast runs outrank low-quality runs. Cost is an operational trade-off, not correctness.
- Treat low quality as eval infrastructure failure. Low scores are valid findings and should produce reports and badcases.

## Consequences

V1 can compare behavior honestly and show trade-offs. Cost and latency remain visible, but candidate discussion starts with quality.

## Implementation Notes

- Quality metrics include failure type exact accuracy, evidence hit rate, required fields completeness, and tool path validity.
- Operational metrics include cost, latency, token usage, step count, and tool call count.
- Per-failure-type score breakdowns are required.
- Formal quality gate status is `pass` or `fail`; debug runs may show gate previews.
- Failure type acceptable alternatives are reported separately from exact accuracy.
- Required fields completeness checks presence, type correctness, non-empty required content, legal enum values, valid evidence references, bounded confidence, and minimal action specificity.

## Consolidates

Micro ADRs: `0027`, `0028`, `0029`, `0030`, `0031`, `0032`, `0063`, `0064`, `0109`, `0110`, `0111`.
