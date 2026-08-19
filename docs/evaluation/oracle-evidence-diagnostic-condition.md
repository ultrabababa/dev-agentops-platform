# Oracle Evidence Diagnostic Condition 与 Agent-System Realization Gap

> Current-state note (2026-08-19): Oracle Evidence execution 与 L4 `self_built_react` formal milestone 都已经完成。此前“等待真实 L4 formal artifact 再做 generic pairing / realization gap”的 sequencing guard 已满足。Pair Validator 与 gap-report machinery 仍**尚未实现**，但现在是当前可执行的下一阶段，而不是被前置条件阻塞的 future work。

Oracle Evidence answers：

> 当 Human-reviewed Minimal Sufficient Evidence Set 已经直接提供给固定模型时，它能否按同一 diagnosis/report contract 完成当前 Case？

Oracle 是与 L0–L5+ capability ladder 正交的 diagnostic intervention，不是 Product Runtime，也不是 rung。

## 1. Current Oracle implementation

```text
frozen required_evidence_ids
    -> Trusted Oracle resolver
    -> Canonical coordinates
    -> resolve source-faithful Physical Artifact content
    -> deterministic Oracle Runtime Input
    -> fixed MiniMax-M3 one-shot diagnosis
    -> existing Structured Triage Report scorer
```

已实现并验证：

- deterministic Oracle Evidence Item/Pack resolution；
- source-content SHA-256 verification；
- evaluator leakage guard / answer-neutral model-visible envelope；
- explicit versioned `evidence_delivery` Treatment identity；
- Matrix v2 formal scheduler / persistence / Trace integration；
- exact context preflight for the Oracle condition；
- one model call per Sample；
- 20 Case × 3 repeat formal milestone；
- historical L1/L2 identities preserved。

Current tracked milestone: [Oracle MiniMax-M3 Full-Suite Milestone](milestones/oracle-minimax-m3-full-suite-2026-08-15.md).

## 2. What Oracle changes

A normal Agent/System result mixes at least two stages：

```text
Evidence acquisition / selection / context construction
    -> diagnosis / report synthesis
```

Oracle intentionally removes ordinary evidence-discovery difficulty by supplying only the reviewed Required Evidence source content. It does **not** supply the answer.

Oracle input may contain：

- Stable Evidence IDs；
- resolved raw-log spans；
- resolved repository-file spans and paths；
- deterministic source-faithful ordering/envelope。

Oracle must never expose：

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

This is a curation/review property, not something retroactively tuned until the Oracle model passes.

## 4. Formal milestone status

### Oracle

The preserved Oracle MiniMax-M3 formal milestone used frozen `triage-suite-v1`：

```text
20 Cases × 3 repeats
= 60 Samples
= 60 model calls
= 60/60 scored
= 0 execution failures
```

Key Suite metrics：

```text
Failure Type Exact Match = 85.00%
Evidence Hit Rate        = 89.29%
Protocol Validity        = 100.00%
```

### L4

The corresponding L4 MiniMax-M3 milestone now exists：

```text
20 Cases × 3 repeats
= 60 planned Samples
= 59 scored
= 1 provider execution failure
```

Key Suite metrics：

```text
Execution Coverage       = 98.33%
Failure Type Exact Match = 88.33%
Evidence Hit Rate        = 65.51%
Protocol Validity        = 81.36%
```

See [L4 MiniMax-M3 Full-Suite Milestone](milestones/l4-minimax-m3-full-suite-2026-08-19.md).

The existence of both artifacts enables pairing analysis, but does **not** by itself prove that every metric difference is a clean causal “Oracle minus Agent” estimate. Compatibility still has to be validated explicitly.

## 5. Pairing with L4

Oracle-vs-L4 should be paired only when declared controls match sufficiently, including where applicable：

- same Suite / Case versions and fingerprints；
- same base model/provider/profile；
- same diagnosis Task Contract / output contract / scorer；
- compatible reasoning and generation settings；
- explicit known wrapper/Treatment differences；
- compatible repeat/sample semantics and visible execution coverage。

The intended analysis question is：

> Given the same model and diagnosis contract, how much of the evidence-conditioned diagnosis capability is realized by the actual Agent System that must investigate the Case itself?

If additional behavior-affecting differences are uncontrolled, report the comparison as a **combined difference** rather than a formal realization-gap pair.

## 6. Agent-System Realization Gap

For a higher-is-better diagnosis metric `m`：

```text
realization_gap(case, m)
  = oracle_score(case, m) - agent_score(case, m)
```

Gap remains a metric vector, never one composite capability score.

Report at least：

```text
per Case
per Failure Type
Suite aggregate
repeat / variance information
pairing identity and compatibility result
```

Do not fold acquisition/operational metrics such as tool-call count, steps, cost or latency into a purported model-capability score. Those are explanatory signals for why the Agent did or did not realize Oracle-condition performance.

A negative gap on one diagnosis metric is possible and not inherently invalid. For example, L4 Suite Failure Type Exact Match (`88.33%`) is higher than Oracle (`85.00%`). Oracle is not a theoretical upper bound; it is a specific evidence-delivery intervention.

## 7. Gap attribution using L4 trajectory

The value of pairing is not only the numeric difference. L4 has a complete Agent trajectory, so gap analysis can distinguish several failure mechanisms：

```text
A. required / decisive physical content never entered model-visible history
   -> evidence acquisition / tool-use problem

B. decisive physical content was observed but correct Canonical ID was not cited
   -> citation mapping / evidence selection / final report problem

C. decisive evidence was available/cited but diagnosis remained wrong
   -> reasoning / causal-chain problem
```

The first L4 milestone already suggests that class B is important: unknown/invented Evidence IDs dominated protocol-invalid final reports.

This is more actionable than treating every Oracle-L4 difference as generic “Agent weakness”.

## 8. Relationship to L4 Canonical-coordinate visibility

Oracle source selection remains a hidden Ground Truth intervention. L4 separately receives the complete **answer-neutral Canonical coordinate vocabulary** at episode start purely as citation vocabulary.

These are not equivalent：

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

## 9. Current implementation target

The next implementation slice should remain small：

```text
Pair Validator
    -> validate compatible Oracle / L4 formal runs
    -> construct Case-level pairs
    -> preserve execution-failure visibility

Realization Gap report
    -> metric-vector delta per Case
    -> Failure-Type aggregation
    -> Suite aggregation
    -> repeat / variance view

Badcase attribution support
    -> join L4 trajectory / Trace evidence
    -> classify acquisition vs mapping/report vs reasoning
```

Do **not** reimplement Oracle Runner, redesign the L4 Runtime, or silently normalize away protocol/execution failures as part of the gap machinery.

A formal Diagnosis Pass Predicate / quadrant visualization may be added only if it provides additional analytical value beyond the metric-vector report; it is not required for the first Pair Validator slice.

## 10. Related decisions and results

- [ADR 0124: Oracle Evidence Diagnostic Condition](../adr/0124-oracle-evidence-diagnostic-condition.md)
- [ADR 0125: Formal Evaluation Evidence Universe and Access](../adr/0125-formal-evaluation-evidence-universe-and-access.md)
- [ADR 0126: Offline Case Schema V2](../adr/0126-offline-case-schema-v2-physical-artifacts-and-canonical-evidence.md)
- [ADR 0128: L4 Self-built ReAct Runtime Contract](../adr/0128-l4-self-built-react-runtime-contract.md)
- [ADR 0129: L4 Provider-Reported Context Accounting](../adr/0129-l4-provider-reported-context-accounting.md)
- [Formal Evaluation Methodology](formal-evaluation-methodology.md)
- [Oracle MiniMax-M3 Full-Suite Milestone](milestones/oracle-minimax-m3-full-suite-2026-08-15.md)
- [L4 MiniMax-M3 Full-Suite Milestone](milestones/l4-minimax-m3-full-suite-2026-08-19.md)
