# Formal Evaluation Evidence Universe and Access

## Status

Accepted.

## Context

An Offline Case Package can remain structurally valid while its Agent-visible evidence has been curated down to almost exactly the items referenced by `required_evidence_ids`. In that shape, a normal Fixed Pipeline, Retrieval, or ReAct condition begins too close to the Oracle Evidence condition: the curator has already performed evidence localization before the episode starts.

This collapse weakens the experiment's ability to measure evidence localization, query formulation, retrieval, tool selection, adaptive investigation, context management, natural-distractor rejection, and stopping decisions. It also confuses physical Case artifacts with the stable evidence coordinates used by runtimes and scorers.

## Decision

Each Formal Case defines one frozen, offline, authentic, bounded-but-realistic **Evidence Universe**. The runtime-facing view of that universe is the **Investigation Workspace**. For the first Formal Suite, it contains a complete or naturally bounded historical log and the exact failing or otherwise relevant revision's bounded repository snapshot. It may contain natural neighboring information and distractors, but curators must not add synthetic irrelevant noise merely to manufacture difficulty or reduce the universe to the known root-cause region. Project Knowledge is not part of the Case Evidence Universe; a future experiment may introduce it as an independently versioned runtime or retrieval input.

Physical artifacts are deterministically mapped to answer-neutral **Canonical Evidence Units**. These units address source spans within the Evidence Universe and provide the common coordinates for indexing, tool results, trace observations, citations, Retrieval Evidence Hit, Report Evidence Hit, and Oracle pack construction. One physical log or repository file may produce multiple units. Stable IDs must describe source identity or location without encoding evaluator conclusions.

A Trusted Evaluator artifact identifies a hidden, Human-reviewed, inclusion-minimal sufficient subset of Canonical Evidence Units. It contains the facts necessary to derive the Expected Diagnosis without containing evaluator-authored Failure Type, Root Cause, Fix, Tool Path, scorer label, or curator reasoning. The normal Agent-visible corpus must be materially broader than this subset; ordinary conditions must not receive the curated Required Evidence set at episode start.

The Case Package defines what exists in the evaluation world. The **Evidence Acquisition Condition** defines how a runtime may observe and investigate that world:

- Fixed Pipeline uses a deterministic fixed flow, heuristic, or fixed top-k selection and has no autonomous investigation loop.
- Retrieval queries the Canonical Evidence corpus and supplies static retrieval results to the fixed model, without a full autonomous investigation loop.
- ReAct adaptively searches and opens the Investigation Workspace, chooses follow-up actions, manages context, and decides when to stop.
- Oracle Evidence bypasses ordinary discovery and directly supplies the reviewed Required Evidence subset under ADR 0124.

Controlled comparisons keep the Case, Evidence Universe, Expected Answer, scorer, and base model fixed wherever applicable. Evidence acquisition and runtime scaffold are the intended experimental variables; not every condition must have identical search/open tools.

Retrieval Evidence Hit means the trace proves that a runtime retrieved or inspected a required Canonical Evidence Unit. Report Evidence Hit means the final Structured Triage Report cited a required Canonical Evidence Unit. They remain separate so evaluation can distinguish not found, found but unused, and found and cited.

## Alternatives Considered

- Curate only answer-relevant evidence. This makes Case construction perform the investigation and collapses normal conditions toward Oracle.
- Require the entire upstream repository and complete unbounded CI history. This is costly, unnecessary, and can make difficulty depend on corpus size rather than the failure.
- Add synthetic noise or a fixed noise ratio. This manufactures benchmark difficulty and does not reflect authentic investigation.
- Use a universal chunk size, chunk count, file count, or line window. Natural artifact structure differs across Cases, so one threshold would become an accidental semantic rule.
- Give every condition the same search/open interface. Evidence acquisition is itself an experimental variable; forcing identical access would erase the distinction being measured.

## Consequences

Positive consequences:

- Retrieval and ReAct uplift can be measured without curator-provided localization.
- Oracle remains a meaningful evidence-conditioned diagnostic rather than a near-copy of a normal condition.
- Stable evidence hits, citations, and traces remain comparable across runtimes.
- Frozen offline evaluation remains reproducible.

Tradeoffs:

- Formal Case Packages can be larger.
- Runtime and retrieval implementations must actually exploit searchable artifacts.
- Human review must assess universe bounds, canonical coverage, ID neutrality, and absence of manufactured distractors.
- Snapshot and unit counts can legitimately vary by Case.
- The first 20 Formal Case Packages must wait for Schema V2 implementation instead of being frozen under Schema V1.

## Non-Decisions

- No universal chunk size, unit count, repository file count, noise ratio, or line-window rule is defined.
- A Case need not include the entire upstream repository or an unbounded log history.
- Not every runtime must provide search/open tools or an adaptive loop.
- Constructed Cases remain allowed; only artificial irrelevant distractors added solely to create difficulty are forbidden.
- The five V1 Failure Types, diagnosis-only product boundary, and deterministic scoring semantics do not change.
- No runtime, retrieval, tool, index, or Oracle execution is implemented by this decision.
- No Project Knowledge artifact is added to the Formal Case Package.

## Structural Schema Consequence

This methodology exposed a structural limitation in Offline Case Schema V1. Logs have a physical source (`raw.log`) and separately frozen chunks, but repository content exists only as `repository-evidence.json`. The physical repository Investigation Workspace, Canonical Evidence coordinates, and evaluator evidence labels are therefore not cleanly separated.

Offline Case Schema V2 is required before the first Formal Suite freezes its 20 Case Packages. Schema V2 must separate Physical Artifacts, Canonical Evidence, and Trusted Evaluator Artifacts; represent the physical repository snapshot independently; and make Canonical Units resolve machine-readable source spans instead of acting as independent fact copies. This ADR establishes the methodology but does not define the complete storage schema. [ADR 0126](0126-offline-case-schema-v2-physical-artifacts-and-canonical-evidence.md) records the accepted storage and trust-layer decision.

## Implementation Guide

See [Formal Evaluation Methodology: Evidence Universe and Access Conditions](../evaluation/formal-evaluation-methodology.md).

## Refines

ADRs: `0113`, `0115`, `0118`, `0122`, `0123`, `0124`.
