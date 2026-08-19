# Formal Evaluation Methodology：Evidence Universe、Schema V2 与 Access Conditions

> Current-state note (2026-08-19): `triage-suite-v1`、20 个 Schema V2 Cases 与 Canonicalization Profile v1 已冻结；historical L1/L2/Oracle/L4 milestones、Oracle↔L4 Pair Analysis、shared deterministic Evidence Reference Canonicalization、fresh four-condition canonicalized generation，以及 L4 Batch + Parallel Tool Policy initial + replication experiment 均已完成。Batch + Parallel 是 new L4 evaluations 的推荐 Tool Policy；historical single/sequential 保留为 immutable reference。

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

The first Formal Suite uses one frozen suite-shared Canonicalization Profile v1. Changing Canonical coordinates/required IDs in the frozen suite is a Case/Suite identity change, not a Runtime tweak.

## 5. Investigation Workspace

The Investigation Workspace is the Runtime-facing physical view of the Case world. For L4 it is conceptually:

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
| L1 Full-context One-shot | complete Agent-visible physical universe upfront | no | historical + canonicalized fresh generation complete |
| L2 Fixed Model Workflow | fixed program-controlled multi-stage input flow | no | historical + canonicalized fresh generation complete |
| L3 Static Retrieval | versioned static retrieval over Physical Artifacts | no | not implemented; optional diagnostic |
| L4 self-built ReAct | `read/grep/find/ls` investigation of physical workspace | yes | historical/fresh milestones + Batch/Parallel replication complete |
| Oracle Evidence | Trusted resolver supplies reviewed Required Evidence source content directly | no | historical + canonicalized fresh generation complete |

L0–L5+ is not mandatory implementation order. Oracle is orthogonal to the ladder.

## 7. L4 Canonical-coordinate vocabulary and shared final-report normalization

A normal Agent must never receive a curator-selected **Required Evidence menu**.

L4 may receive the complete **answer-neutral Canonical coordinate vocabulary** in the initial model-visible input so the final report can cite valid Evidence IDs.

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

L4 still has to discover decisive physical content through tools.

Historical L4 showed that final citation representation can fail even when investigation/diagnosis is useful. Pair Analysis therefore moved the deterministic repair to shared final-report/output infrastructure rather than adding an L4-only coordinate helper.

Current shared path:

```text
runtime-specific model execution
    -> raw candidate document
    -> deterministic Evidence Reference Canonicalization
    -> report validation
    -> frozen scorer
```

Resolver semantics are deliberately narrow:

- exact frozen Canonical ID -> preserve;
- matching frozen source identity + parseable explicit line range -> map by deterministic physical overlap to frozen Canonical unit(s);
- stably deduplicate resolved references;
- unresolvable reference -> remain invalid.

The resolver must not inspect Required Evidence, Expected Answer, evaluator labels/reasoning, semantic similarity, or fuzzy path matching. It also does not add a trajectory/read-history proof obligation solely for normalized references. The Runtime normalizes representation; it does not choose which evidence the model ought to cite.

Historical raw candidate replay is the causal isolation evidence because model output is held fixed. Fresh generation is operational confirmation and is subject to hosted regeneration variance.

## 8. L4 Tool Policy as an explicit Treatment

Tool availability comes from the frozen Tool Registry; Tool Policy controls cross-call execution semantics.

Historical reference:

```text
call_mode = single
execution_mode = sequential
multiple_calls = reject_all_with_error_results
```

Recommended forward L4 Treatment:

```text
call_mode = batch
execution_mode = parallel
multiple_calls = accept_independently
```

Batch + Parallel keeps `runtime_variant=self_built_react`; it is not a new capability rung. Frozen semantics include:

- zero/one/multiple ToolCalls in one Model Decision;
- no arbitrary ordinary ToolCall count cap;
- malformed / expected errors isolated per call;
- valid siblings execute concurrently;
- duplicate calls are not deduplicated;
- barrier before next Model Decision;
- ToolResults materialize in original model-authored order;
- one N-call Model Decision consumes one Agent step;
- unexpected Runtime/workspace/tool defects remain Sample-level infrastructure failures;
- `stop_reason=length` executes none;
- the Runtime-control prompt exposes batching neutrally rather than forcing it.

The initial Batch run and a fresh back-to-back replication are complete. Model Decision reduction reproduced at about `31–35%`; the clean replication also reduced wall time `17.54%` while executed ToolCalls changed only `809 -> 775`. The initial apparent quality regression did not reproduce. Therefore the current recommendation is Batch + Parallel for new L4 evaluations while historical single/sequential remains an immutable comparison reference.

## 9. Context/accounting semantics by condition

### L1/L2/Oracle

These formal MiniMax paths retain their existing exact-token behavior where defined. In particular, L1 full-context identity forbids silent truncation: if its complete serialized input plus reserved completion is infeasible, it must fail rather than silently become a different condition.

### L4

ADR 0129 supersedes mandatory local exact-token preflight for L4 only.

```text
build logical request
    -> provider-request execution
    -> successful provider usage
    -> record provider-reported input tokens
```

Current identity:

```text
assessment = provider_reported
method = provider_response_usage
policy = observe_provider_usage_no_local_preflight
```

L4 performs no compaction, summarization, trimming or automatic context compression. A provider context-limit rejection is observed as provider/execution evidence rather than predicted by a local exact replica.

## 10. Oracle semantics and Oracle↔L4 Pair Analysis

Oracle bypasses ordinary evidence discovery by resolving the hidden reviewed Required Evidence set to source-faithful Physical Artifact content. It may include stable IDs but never exposes `required` labels, Expected Answer fields, curator reasoning or scorer answers.

Oracle↔L4 Pair Analysis is implemented and complete. It validates compatible Suite/Case, model and scoring identities; compares at Case aggregate; preserves condition-local repeats rather than pairing repeat indexes; and keeps execution coverage separate from scored quality.

Human/AI review showed multiple distinct mechanisms rather than one generic realization gap:

```text
Canonical reference / report realization
Investigation depth / evidence acquisition
Evidence selection
Causal reasoning
Operational execution reliability
```

Negative-gap Cases demonstrate that autonomous L4 investigation can add causal-diagnosis value rather than merely approximating Oracle evidence delivery.

## 11. Evidence-hit and badcase interpretation

Current Report Evidence Hit is based on final cited Canonical Evidence IDs against hidden Required Evidence IDs under the frozen scorer.

For Human/AI analysis, keep these conceptual failure classes distinct:

```text
A. decisive physical content never found / seen
   -> acquisition / tool-use problem

B. physical content found but correct Canonical ID not cited
   -> mapping / evidence-selection / report problem

C. correct ID cited / decisive evidence available but diagnosis wrong
   -> reasoning / diagnosis problem
```

These are analysis lenses only, not persisted Pair Analyzer labels or automatic rule-engine outputs.

Shared Evidence Reference Canonicalization addresses only the deterministic representation subset of B. It does not solve missing acquisition, missing evidence selection, or causal reasoning errors.

## 12. Comparison and causal-interpretation boundary

For higher-is-better diagnosis metric `m`:

```text
realization_gap(case, m)
  = oracle_score(case, m) - agent_score(case, m)
```

Gap must remain a metric vector. Do not collapse classification, Evidence Hit, report completeness, protocol validity, cost, latency and tool behavior into one composite score.

A valid controlled comparison checks, where applicable:

- same Suite / Case versions and fingerprints;
- same base model/provider/profile;
- same diagnosis Task Contract / output contract / scorer;
- compatible reasoning/generation settings;
- explicit Treatment differences;
- repeat/sample availability and execution coverage.

If controls differ beyond the intended intervention, report a **combined difference** instead of pretending to have isolated a single causal effect.

Hosted fresh generations are not deterministic causal controls even at temperature 0. The Batch experiment therefore relies on replication: quality deltas were unstable and changed direction, while the efficiency mechanism reproduced. Paired Case-level intervals are diagnostic uncertainty summaries, not leaderboard significance claims.

Operational signals such as tool count, steps, token usage and latency are explanatory features, not components of a model-capability score.

## 13. Reproducibility boundaries

Formal comparisons must preserve or explicitly version:

- Suite/Case identity;
- Evidence/Diagnosis Ground Truth;
- scorer/report/output-realization contract;
- provider/model/inference settings;
- runtime/evidence-delivery Treatment;
- Component fingerprints;
- Execution Policy;
- code revision / dirty state.

A result with multiple changed controls is a combined difference, not evidence of one isolated causal uplift.

Historical formal artifacts must remain attached to the contracts that actually produced them. Shared canonicalization and Batch + Parallel each created new explicit Treatment/output identities; neither retroactively rewrites historical metrics/fingerprints.

A `git_dirty=true` manifest remains visible provenance. For the Batch experiment, maintainer verification established that the observed dirty state came from an unrelated untracked `.worktrees/` directory while tracked files matched the recorded revision; this was documented rather than hidden by rerunning solely to flip the metadata bit.

## 14. Current measurements and next direction

Completed measurement sequence:

1. historical L1/L2/Oracle/L4 formal milestones;
2. Oracle↔L4 Pair Analysis;
3. shared canonicalizer implementation;
4. zero-model-cost historical replay;
5. fresh L1/L2/Oracle/L4 canonicalized `20×3` generation;
6. L4 Batch + Parallel initial `20×3` formal run;
7. fresh back-to-back single/sequential vs Batch + Parallel replication.

The Batch experiment is now complete. Current evidence supports Batch + Parallel as the recommended forward L4 Tool Policy, with small Evidence Hit / Protocol deltas retained as weak residual signals to monitor rather than demonstrated regressions.

The next large Runtime capability direction is executable repair / sandboxed remediation:

```text
investigate -> diagnose -> mutate/edit -> execute/test -> observe -> retry -> verify -> report
```

This is outside the completed read-only V1 boundary and must be introduced as a distinct new phase. L3 retrieval, compaction, planner/verifier, memory, skills/MCP and multi-agent remain evidence-gated rather than bundled automatically.

## 15. Source-of-truth order

For current behavior use:

1. [Active ADR Index](../adr/README.md);
2. `README.md` / `CONTEXT.md` current-facing orientation;
3. this methodology for current evidence/trust/comparison semantics;
4. ADR 0128 for the frozen historical L4 V1 Runtime contract + ADR 0129 for L4 context accounting;
5. current Matrix / Registry / source-code contracts;
6. [L4 Batch + Parallel ToolCalls Milestone](milestones/l4-batch-parallel-toolcalls-2026-08-19.md) for the current L4 Tool Policy recommendation and replication evidence;
7. [Shared Evidence Reference Canonicalization Milestone](milestones/evidence-reference-canonicalization-2026-08-19.md) for the completed output-resolution decision;
8. [Oracle ↔ L4 Pair Analysis Findings](milestones/oracle-l4-pair-analysis-2026-08-19.md) for historical badcase-driven analysis;
9. [Milestone Status Index](milestones/README.md) before interpreting any other dated milestone;
10. dated calibration/review/milestone docs only for historical facts and immutable experiment results.

Historical milestone forward-looking recommendations may be superseded; their measured results and run identities remain historical evidence.