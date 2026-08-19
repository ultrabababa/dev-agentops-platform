# Formal Evaluation Methodology：Evidence Universe、Schema V2 与 Access Conditions

> Current-state note (2026-08-19): `triage-suite-v1`、20 个 Schema V2 Cases 与 Canonicalization Profile v1 已冻结；L1/L2/Oracle/L4 MiniMax-M3 formal milestones 均已完成。L4 access semantics 由 ADR 0128 定义，context-accounting amendment 由 ADR 0129 定义。真实 L4 artifact 已存在，因此 Oracle-vs-L4 pairing / realization-gap analysis 不再被“缺少 Agent artifact”阻塞。

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

这条边界是整个 Formal Evaluation 的基础：Runtime 可以改变如何获取证据，但不能改变什么是事实源、什么是 hidden Ground Truth。

## 2. Evidence Universe

A Formal Case defines one authentic, frozen, offline, bounded-but-realistic Evidence Universe:

```text
complete or naturally bounded historical CI/test log
+
bounded repository snapshot from the exact failing/relevant revision
```

The universe is chosen from a plausible investigation neighborhood visible from the failure, not by reverse-engineering the curator-known answer. It may contain authentic neighboring information and natural distractors. Do not manufacture synthetic noise or reduce the universe to only root-cause evidence.

Passing/fix revisions, PR discussion, curator notes and other answer-validation material remain outside the Agent-visible Case world.

Project Knowledge is not a Physical Artifact in `triage-suite-v1`; it can be introduced later only as an independently versioned Runtime/Retrieval Treatment.

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
       -> stable citation / measurement coordinates

Physical Artifact
    -> optional Runtime Retrieval Chunker
       -> runtime-specific chunks / search results
```

Do not equate Canonical Units with retriever index chunks.

### Evaluator artifacts

`required-evidence.json` is the only Evidence Ground Truth source. `expected-answer.json` is Diagnosis Ground Truth. Neither is directly readable by normal Agent/Runtime paths.

## 4. Canonicalization Profile v1

The first Formal Suite uses one frozen suite-shared Canonicalization Profile v1. Earlier documents that describe profile calibration or `N=100` as only a candidate reflect pre-freeze history.

Changing Canonical coordinates/required IDs in the frozen suite is a Case/Suite identity change, not a Runtime tweak.

## 5. Investigation Workspace

The Investigation Workspace is the Runtime-facing physical view of the Case world. For L4 V1 it is conceptually:

```text
/raw.log
/repository/...
```

Package internals, canonical-evidence files, repository-manifest metadata and evaluator artifacts are not tool-readable.

Different conditions may expose the same underlying Case world differently because evidence acquisition/delivery is itself an experimental variable.

## 6. Condition access semantics

| Condition | Physical evidence delivery / acquisition | Adaptive Agent loop? | Current state |
| --- | --- | --- | --- |
| L0 Pipeline | deterministic program-defined access | no | implemented |
| L1 Full-context One-shot | complete Agent-visible physical universe upfront | no | formal milestone complete |
| L2 Fixed Model Workflow | fixed program-controlled multi-stage input flow | no | formal milestone complete |
| L3 Static Retrieval | versioned static retrieval over Physical Artifacts | no | not implemented; optional diagnostic |
| L4 self-built ReAct | `read/grep/find/ls` investigation of physical workspace | yes | formal milestone complete |
| Oracle Evidence | Trusted resolver supplies reviewed Required Evidence source content directly | no | formal milestone complete |

L0–L5+ is not mandatory implementation order. Oracle is orthogonal to the ladder.

## 7. L4 Canonical-coordinate vocabulary

Earlier methodology correctly rejected giving a normal Agent a curator-selected **Required Evidence menu**. That remains forbidden.

ADR 0128 makes a narrower L4 decision: the complete **answer-neutral Canonical coordinate vocabulary** is included in L4's initial model-visible user input so the final report can cite valid Evidence IDs.

The distinction is critical:

```text
L4 receives upfront:
- all answer-neutral coordinate IDs / source spans

L4 does NOT receive upfront:
- physical source content
- required / optional labels
- which coordinates matter
- Expected Answer
- evaluator reasoning / metadata
```

L4 still has to discover decisive physical content through tools and map observed facts to neutral coordinates itself.

The first L4 formal milestone empirically validates that this mapping is a meaningful capability boundary: unknown/invented Evidence IDs dominated protocol-invalid reports even when the model had inspected relevant physical spans.

No dynamic hidden Runtime span -> Evidence-ID repair exists in the L4 V1 baseline.

## 8. Context/accounting semantics by condition

### L1/L2/Oracle

These formal MiniMax paths retain their existing exact-token behavior where defined. In particular, L1 full-context identity forbids silent truncation: if its complete serialized input plus reserved completion is infeasible, it must fail rather than silently become a different condition.

### L4

ADR 0129 supersedes mandatory local exact-token preflight for L4 only.

L4 behavior：

```text
build logical request
    -> provider-request execution
    -> successful provider usage
    -> record provider-reported input tokens
```

Current identity：

```text
assessment = provider_reported
method = provider_response_usage
policy = observe_provider_usage_no_local_preflight
```

L4 V1 performs no compaction, summarization, trimming or automatic context compression. A provider context-limit rejection is observed as provider/execution evidence rather than predicted by a local exact replica.

The first formal L4 milestone observed maximum provider-reported input of `98,893` tokens and no context-limit rejection.

## 9. Oracle semantics

Oracle bypasses ordinary evidence discovery by resolving the hidden reviewed Required Evidence set to source-faithful Physical Artifact content. It may include stable IDs but never exposes `required` labels, Expected Answer fields, curator reasoning or scorer answers.

Oracle MiniMax-M3 20×3 formal milestone：

```text
60/60 scored
0 execution failures
Evidence Hit Rate = 89.29%
```

L4 MiniMax-M3 20×3 formal milestone now also exists：

```text
59/60 scored
Execution Coverage = 98.33%
Failure Type Exact Match = 88.33%
Evidence Hit Rate = 65.51%
Protocol Validity = 81.36%
```

Therefore the previous sequencing guard — “do not implement generic Oracle-vs-L4 gap analysis before a real L4 artifact exists” — is satisfied.

The next analysis layer should not simply subtract Suite aggregates. It must first validate pairing identity and then compute metric-vector gaps by Case / Failure Type with repeat variance preserved.

## 10. Evidence-hit and badcase interpretation

Current Report Evidence Hit is based on final cited Canonical Evidence IDs against hidden Required Evidence IDs under the frozen scorer.

For analysis, keep these failure classes distinct：

```text
A. decisive physical content never found / seen
   -> acquisition / tool-use problem

B. physical content found but correct Canonical ID not cited
   -> mapping / evidence-selection / report problem

C. correct ID cited / decisive evidence available but diagnosis wrong
   -> reasoning / diagnosis problem
```

This distinction becomes especially important after L4 because Agent trajectories let us inspect whether the required source content actually entered the model-visible conversation before the final report.

L4 baseline does not add a dynamic physical-span -> Canonical-ID annotation helper. A future answer-neutral coordinate-assistance ablation is a legitimate experimental variable, but it must be represented as explicit behavior identity rather than silent post-processing.

## 11. Oracle-vs-L4 realization gap boundary

For higher-is-better diagnosis metric `m`：

```text
realization_gap(case, m)
  = oracle_score(case, m) - agent_score(case, m)
```

Gap must remain a metric vector. Do not collapse classification, Evidence Hit, report completeness, protocol validity, cost, latency and tool behavior into one composite score.

A valid pairing must check, where applicable：

- same Suite / Case versions and fingerprints；
- same base model/provider/profile；
- same diagnosis Task Contract / output contract / scorer；
- compatible reasoning/generation settings；
- explicit Treatment differences；
- repeat/sample availability and execution coverage。

If controls differ beyond the intended evidence-acquisition/runtime intervention, report a **combined difference** instead of pretending to have isolated a single causal effect.

Operational signals such as tool count, steps, token usage and latency are useful explanatory features, but not components of a model-capability score.

## 12. Reproducibility boundaries

Formal comparisons must preserve or explicitly version：

- Suite/Case identity；
- Evidence/Diagnosis Ground Truth；
- scorer/report contract；
- provider/model/inference settings；
- runtime/evidence-delivery Treatment；
- Component fingerprints；
- Execution Policy；
- code revision / dirty state。

A result with multiple changed controls is a combined difference, not evidence of one isolated causal uplift.

## 13. Source-of-truth order

For current behavior use：

1. [Active ADR Index](../adr/README.md)；
2. ADR 0128 for the base L4 Runtime contract + ADR 0129 for L4 context accounting；
3. [L4 implementation design](l4-self-built-react-runtime-design.md)；
4. this methodology for general evidence/trust semantics；
5. ADR 0125/0126 for Case/access architecture；
6. current Matrix / Registry / source-code contracts；
7. dated calibration/review/milestone docs only for historical facts and immutable experiment results。

Historical documents should not be rewritten merely because the project advanced; current-facing guidance is responsible for stating what has been superseded.
