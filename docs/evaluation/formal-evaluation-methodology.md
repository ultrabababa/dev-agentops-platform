# Formal Evaluation Methodology：Evidence Universe、Schema V2 与 Access Conditions

> Current-state note (2026-08-18): `triage-suite-v1`、20 个 Schema V2 Cases 与 Canonicalization Profile v1 已冻结；L1/L2/Oracle formal milestones 已完成；L4 access semantics 由 ADR 0128 进一步冻结。本文描述当前通用 evidence/trust methodology，并显式包含 L4 的 Canonical-coordinate vocabulary refinement。

## 1. Trust model

```text
Physical Artifacts
= sole source of facts

Canonical Evidence
= deterministic answer-neutral source coordinates

Evaluator / Required Evidence
= hidden Evidence Ground Truth

Evaluator / Expected Answer
= hidden Diagnosis Ground Truth
```

Normal model-backed conditions never receive evaluator-only labels or answer fields.

## 2. Evidence Universe

A Formal Case defines one authentic, frozen, offline, bounded-but-realistic Evidence Universe:

```text
complete or naturally bounded historical CI/test log
+
bounded repository snapshot from the exact failing/relevant revision
```

The universe is chosen from a plausible investigation neighborhood visible from the failure, not by reverse-engineering the curator-known answer. It may contain authentic neighboring information and natural distractors. Do not manufacture synthetic noise or reduce the universe to only root-cause evidence.

Passing/fix revisions, PR discussion, curator notes and other answer-validation material remain outside the Agent-visible Case world.

Project Knowledge is not a Physical Artifact in `triage-suite-v1`; it can be introduced later only as an independently versioned Runtime/Retrieval treatment.

## 3. Offline Case Schema V2

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

- `raw.log` and manifest-declared repository files are the fact source;
- repository membership is manifest-driven, never discovered silently by directory scan;
- exact revision/provenance and reviewed semantics-preserving sanitization participate in Case identity;
- Agent investigates the frozen Case bytes, not a live upstream checkout.

### Canonical Evidence

Canonical units are deterministic source-span coordinates over Physical Artifacts. Every unit has an answer-neutral stable ID, controlled source path/span and resolved content hash.

Canonicalization is independent of Runtime Retrieval Chunking:

```text
Physical Artifact
    -> Canonicalization Profile
       -> stable citation/measurement coordinates

Physical Artifact
    -> optional Runtime Retrieval Chunker
       -> runtime-specific chunks/search results
```

Do not equate Canonical Units with retriever index chunks.

### Evaluator artifacts

`required-evidence.json` is the only Evidence Ground Truth source. `expected-answer.json` is Diagnosis Ground Truth. Neither is directly readable by normal Agent/Runtime paths.

## 4. Canonicalization Profile v1

The first Formal Suite now uses one frozen suite-shared Canonicalization Profile v1. Earlier documents that describe profile calibration or `N=100` as only a candidate reflect pre-freeze history.

Changing Canonical coordinates/required IDs in the frozen suite is a Case/Suite identity change, not a runtime tweak.

## 5. Investigation Workspace

The Investigation Workspace is the Runtime-facing physical view of the Case world. For L4 V1 it is conceptually:

```text
/raw.log
/repository/...
```

Package internals, canonical-evidence files, repository-manifest metadata and evaluator artifacts are not tool-readable.

Different conditions may expose the same underlying Case world differently because evidence acquisition/delivery is itself an experimental variable.

## 6. Condition access semantics

| Condition | Physical evidence delivery / acquisition | Adaptive Agent loop? |
| --- | --- | --- |
| L0 Pipeline | deterministic program-defined access | no |
| L1 Full-context One-shot | complete Agent-visible physical universe upfront | no |
| L2 Fixed Model Workflow | fixed program-controlled multi-stage input flow | no |
| L3 Static Retrieval | versioned static retrieval over Physical Artifacts | no |
| L4 self-built ReAct | `read/grep/find/ls` investigation of physical workspace | yes |
| Oracle Evidence | Trusted resolver supplies reviewed Required Evidence source content directly | no |

L0–L5+ is not mandatory implementation order. Oracle is orthogonal to the ladder.

## 7. L4 Canonical-coordinate vocabulary refinement

Earlier methodology correctly rejected giving a normal Agent a curator-selected **Required Evidence menu**. That must remain forbidden.

ADR 0128 makes a narrower L4 decision: the complete **answer-neutral Canonical coordinate vocabulary** may be included in L4's initial model-visible user input solely so the final report can cite valid Evidence IDs.

The distinction is critical:

```text
L4 receives upfront:
- all answer-neutral coordinate IDs/source spans

L4 does NOT receive upfront:
- physical source content
- required/optional labels
- which coordinates matter
- Expected Answer
- evaluator reasoning/metadata
```

Thus L4 still has to discover the decisive physical content through tools and map observed facts to neutral coordinates itself.

This avoids a dynamic hidden Runtime mapping helper while preserving the existing scorer/report citation contract. It does not turn Canonical Evidence into a curator-selected evidence corpus.

## 8. L1 full-context semantics

L1 means complete Agent-visible physical evidence in one fixed request and exactly one model call. Silent truncation invalidates the condition identity.

Current formal MiniMax path uses exact preflight. If complete serialized input plus reserved completion cannot fit the configured context capability, it terminates as a context-feasibility execution failure before provider work rather than truncating/summarizing/splitting the condition.

## 9. Oracle semantics

Oracle bypasses ordinary evidence discovery by resolving the hidden reviewed Required Evidence set to source-faithful Physical Artifact content. It may include stable IDs but never exposes `required` labels, Expected Answer fields, curator reasoning or scorer answers.

The Oracle MiniMax-M3 20×3 formal milestone is complete. Generic Oracle-vs-L4 pairing/realization-gap machinery remains deferred until a real L4 formal artifact exists.

## 10. Evidence-hit interpretation

Current report Evidence Hit is based on final cited Canonical Evidence IDs against hidden Required Evidence IDs under the frozen scorer.

For analysis, keep these failure classes distinct:

```text
A. decisive physical content never found/seen
   -> acquisition/tool-use problem

B. physical content found but correct Canonical ID not cited
   -> mapping/evidence-selection/report problem

C. correct ID cited but diagnosis wrong
   -> reasoning/diagnosis problem
```

L4 baseline does not add a dynamic physical-span -> Canonical-ID annotation helper; the model performs that mapping using the upfront neutral coordinate vocabulary.

## 11. Reproducibility boundaries

Formal comparisons must preserve or explicitly version:

- Suite/Case identity;
- Evidence/Diagnosis Ground Truth;
- scorer/report contract;
- provider/model/inference settings;
- runtime/evidence-delivery treatment;
- component fingerprints;
- execution policy;
- code revision / dirty state.

A result with multiple changed controls is a combined difference, not evidence of one isolated causal uplift.

## 12. Source-of-truth order

For current L4 behavior use:

1. ADR 0128;
2. L4 implementation design;
3. this methodology for general evidence/trust semantics;
4. ADR 0125/0126 for Case/access architecture;
5. dated calibration/review/milestone docs only for historical facts.

Historical documents should not be rewritten merely because the project advanced; active guidance must state when those old statuses are superseded.
