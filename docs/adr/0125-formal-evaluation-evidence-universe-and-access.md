# Formal Evaluation Evidence Universe and Access

## Status

Accepted. Refined for L4 by ADR 0128 and for L4 context accounting by ADR 0129.

## Context

A trustworthy Formal Case must not collapse the normal Agent's search space to the curator-known Required Evidence. At the same time, Physical Artifacts, stable citation coordinates and hidden evaluator labels must remain separate concepts.

## Decision

Each Formal Case defines one frozen, offline, authentic, bounded-but-realistic **Evidence Universe** consisting, for the first Formal Suite, of:

```text
complete or naturally bounded historical raw log
+
bounded exact-revision repository snapshot
```

The boundary is chosen from the plausible investigation neighborhood visible from the failure, not by working backward from the known answer. Authentic neighboring information and natural distractors may remain; synthetic irrelevant noise added only to manufacture difficulty is forbidden.

Physical Artifacts are the sole fact source.

They are deterministically mapped to answer-neutral **Canonical Evidence Units**. Canonical Evidence is a measurement/citation coordinate system, not a curator-selected evidence corpus and not mandatory Runtime Retrieval chunks.

Hidden `required-evidence.json` identifies the Human-reviewed inclusion-minimal sufficient Required Evidence subset. Hidden `expected-answer.json` contains Diagnosis Ground Truth. Normal Agent paths cannot read either artifact.

The Case Package defines what exists; each **Evidence Acquisition Condition** defines how that world may be observed.

## Current frozen Suite status

`triage-suite-v1` is frozen with 20 Human-reviewed Schema V2 Cases and the suite-shared Canonicalization Profile v1. Earlier calibration wording in historical docs is not the current state.

## Condition access

- Fixed Pipeline: deterministic program-defined access;
- L1 Full-context One-shot: complete Agent-visible physical universe delivered upfront in one model request;
- L2 Fixed Model Workflow: fixed program-controlled input/stage flow;
- L3 Static Retrieval: optional future versioned static retrieval over Physical Artifacts;
- L4 self-built ReAct: adaptive physical investigation through frozen read-only tools;
- Oracle Evidence: Trusted resolver directly supplies reviewed Required Evidence source content.

The ladder does not require L3 before L4. Oracle is orthogonal to the ladder.

## L4 coordinate-vocabulary refinement

Earlier guidance rejected exposing every Canonical unit as an **answer menu**. ADR 0128 clarifies that this must not be interpreted as a blanket ban on answer-neutral coordinate visibility.

For L4 V1, the complete Canonical coordinate universe is disclosed in the initial model-visible input as **citation vocabulary only**.

L4 still does not receive:

- Physical Artifact content upfront;
- Required/Optional labels;
- which coordinates contain decisive evidence;
- Expected Answer or evaluator reasoning;
- canonical-evidence files through tools.

Physical facts are acquired via `read/grep/find/ls`; the model maps observed facts to the neutral coordinate vocabulary itself.

This is intentionally different from Oracle, which supplies only the reviewed Required Evidence source content and therefore bypasses ordinary discovery.

## Canonicalization vs Runtime Retrieval

Canonicalization and Runtime Retrieval are separate namespaces:

```text
Physical Artifact
    -> Canonicalization Profile
       -> stable coordinates for citation / scoring / identity

Physical Artifact
    -> Runtime-specific Retrieval Chunker
       -> search/index chunks
```

Do not freeze retrieval chunking by reusing Canonical unit boundaries automatically.

## Consequences

Positive:

- normal L4 still measures evidence discovery rather than curator-provided localization;
- final report citations can use the existing frozen scorer contract without hidden Runtime mapping magic;
- Oracle remains meaningfully distinct;
- Case identity stays independent from tool/retrieval design.

Tradeoffs:

- L4 must reason from observed physical content to the correct neutral citation coordinate;
- a complete coordinate vocabulary increases model-visible context and therefore contributes to provider-reported request usage; under ADR 0129 it is **not** guarded by mandatory local exact-token preflight in the L4 Runtime critical path;
- later badcase analysis must distinguish acquisition failure from citation-mapping failure.

The first L4 formal milestone made the second analytical distinction concrete: unknown/invented Evidence IDs were the dominant final protocol failure mode even when the model had inspected relevant physical spans.

## Non-Decisions

This ADR does not define L3 retrieval parameters, L5+ context management, compaction, planning, verifier, memory or skills. Dynamic L4 context-exhaustion semantics remain deferred until observed.

## Implementation Guide

See [Formal Evaluation Methodology](../evaluation/formal-evaluation-methodology.md) and [L4 Self-built ReAct Runtime Design](../evaluation/l4-self-built-react-runtime-design.md).

## Refines

ADRs: `0113`, `0115`, `0118`, `0122`, `0123`, `0124`.

## Refined By

- [ADR 0126: Offline Case Schema V2](0126-offline-case-schema-v2-physical-artifacts-and-canonical-evidence.md)
- [ADR 0127: Staged Runtime Capability Ladder](0127-staged-runtime-capability-ladder-and-reference-boundary.md)
- [ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md)
- [ADR 0129: L4 Provider-Reported Context Accounting](0129-l4-provider-reported-context-accounting.md)
