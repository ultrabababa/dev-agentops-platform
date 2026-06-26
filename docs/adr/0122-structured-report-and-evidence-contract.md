# Structured Report and Evidence Contract

## Status

Accepted.

## Context

Evaluation requires reports that can be validated, scored, and reviewed. Natural-language evidence descriptions are not enough to measure whether the agent found and used the expected evidence.

## Decision

V1 will version the structured triage report schema as an evaluation and product contract outside the component registry. Structured reports must include valid evidence references to stable evidence identifiers. Expected answers distinguish required key evidence from optional evidence, and evidence hit rate means the final report cited expected required evidence.

## Alternatives Considered

- Treat report schema as a mutable agent component. It is a product and scoring contract, not a prompt-like tuning artifact.
- Let reports cite evidence only in prose. This makes evidence hit rate and review unreliable.
- Score retrieval hit and final report citation as one metric. This hides whether the problem is search or report synthesis.

## Consequences

Evidence scoring becomes deterministic and diagnosable. Invalid evidence IDs are hallucinated citations, and retrieval/report gaps can be attributed correctly.

## Implementation Notes

- Report schema version is recorded in run manifests and evaluation methods.
- Evidence references point to log, repository, or project-knowledge evidence IDs.
- Stable evidence IDs are defined by case packages or retrieval corpora.
- Derived evidence is allowed only with provenance back to stable evidence IDs or source spans.
- Retrieval evidence hits and report evidence hits are both reported; primary evidence hit rate is report citation hit.
- Invalid evidence IDs fail evidence-related scoring and produce hallucinated-evidence badcases.

## Consolidates

Micro ADRs: `0102`, `0103`, `0104`, `0105`, `0106`, `0107`, `0108`.
