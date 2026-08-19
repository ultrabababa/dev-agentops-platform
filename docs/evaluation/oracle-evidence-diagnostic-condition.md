# Oracle Evidence Diagnostic Condition 与 Agent-System Realization Gap

> Current-state note (2026-08-19): Oracle Evidence execution 与 L4 `self_built_react` formal milestone 都已经完成。Oracle ↔ Agent Pair Analyzer 现已作为一个小型离线分析能力实现：它直接消费两份 formal `evaluation.json`，按 Case 对齐并计算 `Oracle - Agent` gap；可选读取 Agent SQLite trajectory，为后续 Human / AI badcase 分析提供调查过程。它不是通用 Condition-comparison framework，也不自动做因果归因。

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

## 5. Pairing with L4

The first Pair Analyzer deliberately keeps the comparison contract small. It requires：

- both inputs are `formal_full_suite` artifacts；
- the Oracle side is `model_one_shot` and the other side is a non-Oracle Runtime；
- same Suite fingerprint and same Case identities；
- same model；
- same evaluation method；
- same Structured Triage Report schema version。

This is enough for the current Oracle-vs-L4 analysis question：

> 在同一批 Case、同一个模型和同一评分合同下，模型直接拿到 reviewed key evidence 与 Agent 必须自己调查 evidence 时，结果差多少？

The implementation does not introduce `clean_pair / qualified_pair / incompatible` tiers and does not attempt to become a generic pair-comparison framework.

## 6. Agent-System Realization Gap

For every higher-is-better metric `m`：

```text
realization_gap(case, m)
  = oracle_score(case, m) - agent_score(case, m)
```

Therefore：

```text
gap > 0  -> Oracle performs better
gap = 0  -> same aggregate result
gap < 0  -> Agent performs better on that metric
```

Case aggregate is the primary comparison unit. Repeat index is **not** treated as a strict Oracle-repeat-to-Agent-repeat pair; repeat observations are retained only for stability and badcase interpretation.

The primary realization-gap vector is：

```text
failure_type_exact_match
report_evidence_hit_rate
protocol_validity_rate
```

Auxiliary observations are：

```text
required_fields_completeness
execution_coverage
repeat-level observations
```

Gap remains a metric vector, never one composite capability score. Operational signals such as tool calls or Agent steps remain explanatory information, not capability-score dimensions.

A negative gap is valid. For example, the current L4 Suite Failure Type Exact Match (`88.33%`) is higher than Oracle (`85.00%`). Oracle is a specific evidence-delivery intervention, not a theoretical upper bound.

## 7. Human / AI gap attribution

The Pair Analyzer intentionally stops before causal attribution. It packages the comparison evidence; Human / AI review decides what happened in each important Case.

A useful review lens remains：

```text
A. decisive physical content never entered model-visible history
   -> evidence acquisition / tool-use problem

B. decisive physical content was observed but correct Canonical ID was not cited
   -> citation mapping / evidence selection / final report problem

C. decisive evidence was available/cited but diagnosis remained wrong
   -> reasoning / causal-chain problem
```

These are analysis categories, **not** persisted automatic labels. A Case may involve more than one mechanism, and the first implementation does not build heuristic attribution rules around them.

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

## 9. Current Pair Analyzer

CLI：

```bash
devagentops eval pair \
  --oracle <oracle-evaluation.json> \
  --agent <agent-evaluation.json> \
  --agent-database <optional-agent.sqlite3> \
  --output-dir .devagentops/pair-analysis
```

Outputs：

```text
pair-analysis.json
pair-analysis.md
```

`pair-analysis.json` preserves every Case and repeat observation. If `--agent-database` is supplied, the analyzer also joins persisted Agent trajectory messages for later inspection.

`pair-analysis.md` contains：

- Suite gap；
- Failure-Type gap；
- a compact table covering every Case；
- detailed sections only for Cases with a primary-metric difference, protocol invalidity, or incomplete execution；
- a Human / AI analysis placeholder rather than automatic causal labeling。

The analyzer does not rerun either model, modify Oracle/L4 Runtime behavior, create a new scoring contract, or normalize away execution/protocol failures.

## 10. Related decisions and results

- [ADR 0124: Oracle Evidence Diagnostic Condition](../adr/0124-oracle-evidence-diagnostic-condition.md)
- [ADR 0125: Formal Evaluation Evidence Universe and Access](../adr/0125-formal-evaluation-evidence-universe-and-access.md)
- [ADR 0126: Offline Case Schema V2](../adr/0126-offline-case-schema-v2-physical-artifacts-and-canonical-evidence.md)
- [ADR 0128: L4 Self-built ReAct Runtime Contract](../adr/0128-l4-self-built-react-runtime-contract.md)
- [ADR 0129: L4 Provider-Reported Context Accounting](../adr/0129-l4-provider-reported-context-accounting.md)
- [Formal Evaluation Methodology](formal-evaluation-methodology.md)
- [Oracle MiniMax-M3 Full-Suite Milestone](milestones/oracle-minimax-m3-full-suite-2026-08-15.md)
- [L4 MiniMax-M3 Full-Suite Milestone](milestones/l4-minimax-m3-full-suite-2026-08-19.md)
