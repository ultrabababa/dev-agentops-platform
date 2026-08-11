# Formal Evaluation Evidence Universe and Access

## Status

Accepted.

## Context

An Offline Case Package can remain structurally valid while its Agent-visible evidence has been curated down to almost exactly the items referenced by `required_evidence_ids`. In that shape, a normal Fixed Pipeline, Retrieval, or ReAct condition begins too close to the Oracle Evidence condition: the curator has already performed evidence localization before the episode starts.

This collapse weakens the experiment's ability to measure evidence localization, query formulation, retrieval, tool selection, adaptive investigation, context management, natural-distractor rejection, and stopping decisions. It also confuses physical Case artifacts with the stable evidence coordinates used by runtimes and scorers.

## Decision

Each Formal Case defines one frozen, offline, authentic, bounded-but-realistic **Evidence Universe**. The runtime-facing view of that universe is the **Investigation Workspace**. For the first Formal Suite, it contains a complete or naturally bounded historical log and the exact failing or otherwise relevant revision's bounded repository snapshot. The snapshot boundary is chosen from the plausible investigation neighborhood visible from the failure observation, not by working backward from the curator-known answer. It may contain natural neighboring information and distractors, but curators must not add synthetic irrelevant noise merely to manufacture difficulty or reduce the universe to the known root-cause region. Passing/fix artifacts remain curator-only causal-verification inputs and do not enter the Agent-visible workspace. Project Knowledge is not part of the Case Evidence Universe; a future experiment may introduce it as an independently versioned runtime or retrieval input.

Physical artifacts are deterministically mapped to answer-neutral **Canonical Evidence Units**. Canonical Evidence is the measurement/citation coordinate system, not a curator-selected evidence corpus and not a set of mandatory Retrieval index chunks. For Formal text artifacts, units completely cover the Physical Evidence Universe without gaps or overlaps. Their boundaries and IDs are deterministic, source-faithful, exact-hash verified, and independent of failure lines, fixes, Required Evidence, or curator conclusions. One physical log or repository file may produce multiple units.

Formal Cases will ultimately share a versioned **Canonicalization Profile v1** instead of choosing segmentation independently per Case. B04's complete 100-line repository partition is a calibration example, not a globally frozen constant: `N=100` must be checked against structurally different already-selected Cases before the Profile is frozen.

A Trusted Evaluator artifact identifies a hidden, Human-reviewed, inclusion-minimal sufficient subset of Canonical Evidence Units. It contains the facts necessary to derive the Expected Diagnosis without containing evaluator-authored Failure Type, Root Cause, Fix, Tool Path, scorer label, or curator reasoning. The normal Agent-visible corpus must be materially broader than this subset; ordinary conditions must not receive the curated Required Evidence set at episode start.

The Case Package defines what exists in the evaluation world. The **Evidence Acquisition Condition** defines how a runtime may observe and investigate that world:

- Fixed Pipeline uses a deterministic fixed flow, heuristic, or fixed top-k selection and has no autonomous investigation loop.
- Full-context One-shot supplies the complete Agent-visible Evidence Universe to one fixed Prompt and exactly one model call. It must not silently truncate and still claim full-context semantics; the explicit over-budget outcome is deferred to its implementation design.
- Fixed Model Workflow uses program-controlled fixed stages and model calls without allowing the model to choose an autonomous next-action loop.
- Static Retrieval applies an independently versioned Runtime Retrieval Chunker to Physical Artifacts and supplies retrieval results to a fixed model path, without an autonomous investigation loop. Retrieved physical spans are mapped to overlapping Canonical Evidence IDs for trace/citation/measurement.
- ReAct adaptively searches and opens the Investigation Workspace, chooses follow-up actions, manages context, and decides when to stop.
- Oracle Evidence bypasses ordinary discovery and directly supplies the reviewed Required Evidence subset under ADR 0124.

Full-context One-shot, Fixed Model Workflow, and Static Retrieval are diagnostic/comparison conditions, not additional V1 Product Runtimes. Oracle is orthogonal to the L0-L5+ capability ladder rather than another rung. The ladder does not require Static Retrieval to be implemented before ReAct.

Canonicalization and Runtime Retrieval Chunking are separate responsibilities. Retrieval chunk size, overlap, embedding, index, top-k, and reranking belong to the Runtime/Evidence Acquisition Condition, not to Case curation. Controlled paired per-Case comparisons keep the Case, Evidence Universe, Expected Answer, scorer, and base model fixed wherever applicable, and vary only the target acquisition/runtime condition. Not every condition must have identical search/open tools, but no condition may receive a curator-derived reduction in search space unless that reduction is the explicitly measured intervention.

Retrieval Evidence Hit means the trace's physical observation spans satisfy a Human-frozen attribution rule for the necessary facts represented by Required Evidence. Mapping a span to overlapping Canonical IDs records attribution candidates; arbitrary partial overlap does not automatically count as a full hit. Report Evidence Hit means the final Structured Triage Report cited a required Canonical Evidence Unit under the report contract. They remain separate so evaluation can distinguish not found, found but unused, and found and cited. The V1 observation-attribution rule remains a required Canonicalization calibration output rather than an implicit Schema V2 rule.

## Alternatives Considered

- Curate only answer-relevant evidence. This makes Case construction perform the investigation and collapses normal conditions toward Oracle.
- Require the entire upstream repository and complete unbounded CI history. This is costly, unnecessary, and can make difficulty depend on corpus size rather than the failure.
- Add synthetic noise or a fixed noise ratio. This manufactures benchmark difficulty and does not reflect authentic investigation.
- Freeze B04's `N=100` as a universal repository line window without cross-Case calibration. One Case is insufficient to establish that the parameter is robust across different artifact structures.
- Let each Case choose an arbitrary semantic chunk size. This introduces curator freedom and makes coordinates incomparable; a shared versioned Canonicalization Profile is required before Suite freeze.
- Reuse Canonical Units as mandatory Retrieval chunks. This couples the measurement coordinate system to one Runtime design and can hide curator-derived acquisition advantage.
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
- Canonicalization Profile parameters require cross-Case calibration before the first Suite freeze.

## Non-Decisions

- `Canonicalization Profile v1` and its parameters are not frozen by this ADR; `N=100` remains a candidate repository-text parameter pending calibration.
- Runtime Retrieval Chunking parameters and implementation are not defined by this ADR.
- A Case need not include the entire upstream repository or an unbounded log history.
- Not every runtime must provide search/open tools or an adaptive loop.
- L1 over-budget handling, L2 orchestration stages, L3 retrieval parameters, and their schema representation are not defined by this ADR.
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

## Refined By

[ADR 0127: Staged Runtime Capability Ladder and Reference Boundary](0127-staged-runtime-capability-ladder-and-reference-boundary.md).
