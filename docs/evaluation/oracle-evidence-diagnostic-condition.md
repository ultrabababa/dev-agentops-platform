# Oracle Evidence Diagnostic Condition 与 Agent-System Realization Gap

> Current-state note (2026-08-18): Oracle Evidence execution is **implemented**. The MiniMax-M3 20 Case × 3 formal milestone completed with 60/60 scored Samples and 0 execution failures. What remains deferred is the generic Oracle-vs-Agent pairing / Agent-System Realization Gap machinery until a real L4 formal artifact exists.

Oracle Evidence answers:

> 当 Human-reviewed 的 Minimal Sufficient Evidence Set 已经直接提供给固定模型时，它能否按同一 diagnosis/report contract 完成当前 Case？

Oracle 是与 L0–L5+ capability ladder 正交的 diagnostic intervention，不是 Product Runtime，也不是 rung。

## 1. Current implementation

Current Oracle path:

```text
frozen required_evidence_ids
    -> Trusted Oracle resolver
    -> Canonical coordinates
    -> resolve source-faithful Physical Artifact content
    -> deterministic Oracle Runtime Input
    -> fixed MiniMax-M3 one-shot diagnosis
    -> existing Structured Triage Report scorer
```

已经实现并验证：

- deterministic Oracle Evidence Item/Pack resolution；
- source-content SHA-256 verification；
- evaluator leakage guard / answer-neutral model-visible envelope；
- explicit versioned `evidence_delivery` Treatment identity；
- Matrix v2 formal scheduler / persistence / Trace integration；
- exact context preflight；
- one model call per Sample；
- 20 Case × 3 repeat formal milestone；
- historical L1/L2 identities preserved。

Current tracked milestone: [Oracle MiniMax-M3 Full-Suite Milestone](milestones/oracle-minimax-m3-full-suite-2026-08-15.md).

## 2. What Oracle changes

Normal Agent/system result mixes two stages:

```text
Evidence acquisition / selection / context construction
    -> diagnosis / report synthesis
```

Oracle intentionally removes ordinary evidence discovery difficulty by supplying only the reviewed Required Evidence source content. It does **not** supply the answer.

Oracle input may contain:

- Stable Evidence IDs；
- resolved raw-log spans；
- resolved repository-file spans and paths；
- deterministic source-faithful ordering/envelope。

Oracle must never expose:

- `required` / `optional` labels；
- Expected Answer fields；
- primary/acceptable Failure Type labels；
- curator/reviewer reasoning or selection rationale；
- scorer labels / Quality Gate answers；
- fix commit / passing revision；
- reasonable tool path / reference trajectory / prior eval results。

The fact that the source content was selected is the intervention; no additional answer-like highlighting or summary is allowed.

## 3. Minimal Sufficient Evidence Set

`required_evidence_ids` resolve to a Human-reviewed inclusion-minimal sufficient source-faithful set.

Sufficiency means the set contains the facts necessary to support the Expected Diagnosis under the fixed diagnosis contract. Minimality means removing an item makes at least one necessary fact or disambiguation unavailable.

This is a curation/review property, not something retroactively tuned until the model passes.

## 4. Formal milestone status

The preserved Oracle MiniMax-M3 formal milestone used the frozen `triage-suite-v1`:

```text
20 Cases × 3 repeats
= 60 Samples
= 60 model calls
= 60/60 scored
= 0 execution failures
```

The milestone demonstrated Oracle execution integrity; it did **not** implement or claim a completed Agent-System Realization Gap because the real L4 Agent Product Runtime did not yet exist.

## 5. Pairing with L4

After L4 has a formal artifact, Oracle-vs-L4 can be paired only when the declared controls match sufficiently, including where applicable:

- same Suite / Case versions；
- same base model/provider/profile；
- same diagnosis Task Contract / report contract / scorer；
- same relevant inference settings and output allowance；
- explicit known wrapper/treatment differences。

The intended intervention is evidence acquisition/delivery. If additional behavior-affecting differences are uncontrolled, report the comparison as a combined difference rather than a formal realization-gap pair.

## 6. Agent-System Realization Gap

For a higher-is-better diagnosis metric `m`:

```text
realization_gap(case, m)
  = oracle_score(case, m) - agent_score(case, m)
```

Gap remains a metric vector, never one composite capability score. Report by Case, metric, Failure Type and Suite, together with pairing identities and variance information.

Do not fold acquisition/operational metrics such as tool-call count, steps, cost or latency into a purported “model capability” score. Those are diagnostic signals that help explain why the Agent did or did not realize Oracle-condition performance.

## 7. Relationship to L4 Canonical-coordinate visibility

Oracle source selection is still hidden Ground Truth intervention. L4 ADR 0128 separately allows the **complete answer-neutral Canonical coordinate vocabulary** to be visible at episode start purely as citation vocabulary.

These are not equivalent:

```text
L4:
all answer-neutral coordinates
+ no physical content upfront
+ no required labels
+ Agent discovers facts via tools

Oracle:
only reviewed Required Evidence source content
+ stable IDs
+ no required labels / answer fields
```

Therefore exposing the full coordinate vocabulary to L4 does not collapse L4 into Oracle.

## 8. Deferred work

Still deferred until real L4 formal results exist:

- generic Oracle-vs-L4 Pair Validator；
- formal Diagnosis Pass Predicate if needed for quadrant analysis；
- per-Case/per-Failure-Type realization-gap report machinery；
- variance audit across paired repeats。

Do not reimplement Oracle Runner or redesign the evidence-delivery contract as part of Issue #52 unless a real compatibility defect is found.

## 9. Related decisions

- [ADR 0124: Oracle Evidence Diagnostic Condition](../adr/0124-oracle-evidence-diagnostic-condition.md)
- [ADR 0125: Formal Evaluation Evidence Universe and Access](../adr/0125-formal-evaluation-evidence-universe-and-access.md)
- [ADR 0126: Offline Case Schema V2](../adr/0126-offline-case-schema-v2-physical-artifacts-and-canonical-evidence.md)
- [ADR 0128: L4 Self-built ReAct Runtime Contract](../adr/0128-l4-self-built-react-runtime-contract.md)
- [Formal Evaluation Methodology](formal-evaluation-methodology.md)
