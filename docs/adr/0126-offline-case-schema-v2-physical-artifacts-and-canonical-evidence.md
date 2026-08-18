# Offline Case Schema V2 Physical Artifacts and Canonical Evidence

## Status

Accepted and implemented. The first Formal Suite and Canonicalization Profile v1 are now frozen.

## Context

Schema V1 conflated physical repository material, citation coordinates and evaluator evidence labels. Schema V2 separates source facts, answer-neutral coordinates and hidden Ground Truth so ReAct/Retrieval/Oracle can share one frozen Case world without duplicating facts.

## Decision

Every V2 Case uses three storage/trust layers:

```text
<case-id>/
├── case.json
├── physical-artifacts/
│   ├── raw.log
│   ├── repository-manifest.json
│   └── repository/...
├── canonical-evidence/
│   ├── log-units.json
│   └── repository-units.json
└── evaluator/
    ├── required-evidence.json
    └── expected-answer.json
```

### Physical Artifacts

Physical Artifacts are the sole source of facts. The repository manifest declares exact provenance/revision, frozen membership, path/hash/size integrity and any reviewed semantics-preserving sanitization metadata.

Formal membership is manifest-driven. Runtime must not silently scan additional files into the Case universe.

### Canonical Evidence

Canonical Evidence Units are deterministic, answer-neutral source-span coordinates over frozen Physical Artifacts. Units contain identity/span/hash metadata, not an independently editable fact copy.

Canonicalization is separate from Runtime Retrieval Chunking. Retrieval may use independently versioned chunks and map observations back to Canonical coordinates; Canonical Units are not mandatory index chunks.

### Trusted Evaluator Artifacts

`required-evidence.json` is the only Evidence Ground Truth source. `expected-answer.json` contains Diagnosis Ground Truth. They are separate and evaluator-only.

Oracle Evidence is derived at execution time by resolving Required Evidence IDs through Canonical coordinates to Physical Artifact content. No permanent copied `oracle-evidence.json` is stored.

## Current implementation status

Issue #22 implemented the V2-only Loader, integrity checks, fingerprints, Doctor integration and public leakage boundary. Schema V1 Loader is retired.

Issue #15 subsequently completed the remaining Case construction/review work. Current state:

```text
triage-suite-v1
= 20 frozen Human-reviewed V2 Cases
= 4 Cases per V1 Failure Type

Canonicalization Profile v1
= frozen and enforced for the Suite
```

Therefore older text that says B04 is only a calibration case, `N=100` is merely a candidate, or the shared Profile still needs calibration records pre-freeze project state and is no longer an open decision.

## Runtime visibility is condition-specific

Directory structure defines trust boundaries; a condition defines actual model visibility.

Normal conditions never expose `evaluator/*`.

ADR 0128 further freezes L4 V1 behavior:

- `/raw.log` and `/repository/...` are tool-readable physical workspace;
- canonical-evidence files themselves are not tool-readable;
- the complete answer-neutral Canonical coordinate vocabulary may be included in initial model-visible input for citation;
- Required/Optional labels and Expected Answer remain hidden;
- physical content remains tool-acquired.

This is a Runtime/Evidence Acquisition decision, not a change to Case identity.

## Fingerprints

Case identity covers the V2 manifest, Physical Artifact membership/content, provenance/revision and sanitization metadata, Canonical Evidence definitions/resolved hashes, evaluator Ground Truth and review state. Suite fingerprints compose verified Case identities.

Tool policy, retrieval chunking or L4 observation behavior do not rewrite Case identity; they belong to Runtime/Treatment identity.

## Consequences

- ReAct investigates a real bounded physical workspace;
- Retrieval/Trace/citation/scoring/Oracle share stable source coordinates;
- Evidence and Diagnosis Ground Truth each have one source of truth;
- Runtime experiments can vary without rebuilding the Case package;
- trusted evaluator files remain physically and logically separated.

## Non-Decisions

Schema V2 does not define L3 retrieval parameters, L4 loop/tool policy, L5+ context management, Project Knowledge delivery, or Agent memory. Those are Runtime/Treatment concerns.

## Refines

ADRs: `0115`, `0118`, `0122`, `0123`, `0124`, `0125`.

## Refined By

- ADR 0127 for capability ladder semantics;
- ADR 0128 for concrete L4 visibility/tool behavior.
