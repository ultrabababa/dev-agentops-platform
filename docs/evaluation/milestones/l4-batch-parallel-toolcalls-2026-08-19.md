# L4 Batch + Parallel ToolCalls Milestone — 2026-08-19

> **Status: implementation qualification and fresh replication complete. Batch + Parallel is accepted as the recommended forward L4 Tool Policy for new evaluations; the historical `single + sequential` L4 baseline remains immutable reference evidence.** This milestone records Issue #61 / PR #62, deterministic validation, the initial fresh `20 Cases × 3 repeats` candidate run, a second contemporaneous `single/sequential` vs `batch/parallel` replication block, Runtime-mechanism observations, quality interpretation, and the resulting policy decision. Machine-readable results are preserved in [`l4-batch-parallel-toolcalls-results-2026-08-19.json`](l4-batch-parallel-toolcalls-results-2026-08-19.json).

## 1. Question

Historical and fresh canonicalized L4 traces showed that MiniMax-M3 naturally emitted multiple same-decision ToolCalls even though the frozen historical Runtime-control prompt and Tool Policy required zero-or-one ToolCall and rejected every call in a multi-call decision.

The experiment asks whether L4 should support:

```text
single + sequential + reject-all
        ->
batch + parallel + independent-call handling
```

This is not a new capability-ladder rung. `runtime_variant` remains `self_built_react`; the read-only Tool Registry, workspace, provider/model, canonicalized output contract, scorer, retry semantics, and `max_steps` budget remain unchanged.

## 2. Frozen semantics

Issue #61 froze the candidate behavior before implementation:

- one Model Decision may emit zero, one, or multiple ToolCalls; no artificial ordinary-call count cap;
- existing lightweight call interpretation is performed before execution;
- malformed / expected tool errors are independent per call and do not cancel valid siblings;
- valid sibling calls execute concurrently;
- duplicate calls are not deduplicated;
- the Runtime waits at a barrier for the batch, then appends ToolResults in the model-authored ToolCall order;
- the next Model Decision starts only after that ordered observation is complete;
- one Model Decision consumes one `max_steps` unit regardless of ToolCall count;
- unexpected Runtime/workspace/tool implementation exceptions remain Sample-level infrastructure failures;
- `stop_reason=length` continues to execute none of the returned ToolCalls;
- the matching Runtime-control prompt exposes batching neutrally and does not instruct the model to prefer batching.

## 3. Implementation and deterministic gates

PR #62 adds:

- `l4-batch-parallel-tool-policy-v1`;
- `l4-react-runtime-control-batch-parallel-v1`;
- candidate Matrix `l4-minimax-m3-batch-parallel-canonicalized-v1.json`;
- Runtime support for deterministic parallel execution with an authored-order barrier;
- L4 condition/treatment resolution that accepts either the historical baseline pair or the Batch + Parallel pair without rewriting historical component identities;
- focused regression coverage for actual concurrency, order, duplicate calls, per-call expected errors, infrastructure failure, length truncation, step accounting, component identity, and Matrix validation.

Maintainer-side validation passed:

- focused regression: `29 passed`;
- candidate `eval doctor`: PASS;
- full repository regression: `377 passed, 2 skipped, 30 subtests passed`.

## 4. Initial Batch + Parallel formal run

Initial candidate run:

- Run ID: `010e9a75-8ca8-44b5-8445-d82d188d11f3`
- Status: `completed`
- Suite quality status: `complete`
- Condition: `l4-minimax-m3-batch-parallel-canonicalized-development-v1`
- Code revision: `ae6b756d13471a68c263583533795ef1c2a47231`
- Planned / scored Samples: `60 / 60`
- Execution failures: `0`
- Artifact SHA256: `a8e73a66de70788aa7fc59fce881723ef6e4d75d0127767aa0a4da64765fe67d`

The candidate exercised batching heavily under a neutral prompt:

| Observation | Initial candidate |
| --- | ---: |
| Successful Model Decisions | `547` |
| Provider request attempts | `548` |
| Tool-using decisions | `487` |
| ToolCalls started | `787` |
| Multi-call decisions | `257` |
| Multi-call rate among tool decisions | `52.77%` |
| Samples using at least one multi-call decision | `55 / 60` |
| `multiple_tool_calls_rejected` | `0` |

Batch-size distribution was `1×230`, `2×221`, `3×29`, `4×7`. Expected Agent-visible errors remained isolated (`schema_invalid_arguments=9`, `path_not_found=2`), with no Sample-level Runtime/tool infrastructure failure.

Relative to the earlier fresh canonicalized single/sequential L4 reference (`d6fee1ba-ddd2-4ed3-ae2f-625603de5fef`), successful Model Decisions fell:

```text
798 -> 547
-251
-31.45%
```

Initial formal quality, however, was lower:

| Metric | Fresh canonicalized reference | Initial Batch + Parallel | Delta |
| --- | ---: | ---: | ---: |
| Execution Coverage | 100.00% | 100.00% | 0.00 pp |
| Failure Type Exact Match | 81.67% | 73.33% | -8.33 pp |
| Evidence Hit Rate | 71.83% | 68.19% | -3.64 pp |
| Required Fields Completeness | 99.58% | 86.67% | -12.91 pp |
| Protocol Validity | 93.33% | 86.67% | -6.67 pp |

All eight initial candidate protocol-invalid Samples were `invalid_report_type`; five of those visible outputs still contained the correct `failure_type`. This was diagnostic-only inspection: no Sample was repaired or re-scored.

Because the earlier canonicalization experiment had already demonstrated hosted MiniMax regeneration variance, one fresh A/B observation was insufficient to attribute the quality drop to batching. A contemporaneous replication block was therefore run before changing the L4 recommendation.

### Initial-run long tail

The initial candidate wall time was approximately `1,378.7 s` (`22m58.7s`). The maximum Sample (`odrepair-dubbo-737f7a7e#repeat-2`) took `653.68 s` because one provider attempt hit the frozen `600 s` timeout (`600,160 ms`) and the same logical request then succeeded on retry. The extreme tail is directly explained by provider timeout, not by observed parallel-tool deadlock; no scheduler, ThreadPool, batch-cap, or timeout-policy change was justified.

## 5. Fresh replication block

To test whether the apparent quality drop was reproducible, a new single/sequential canonicalized baseline and a new Batch + Parallel candidate were run back-to-back on the same branch revision, Suite, provider/model configuration, scorer, output resolver, and Execution Policy.

### 5.1 Replication identities

Single/sequential reference:

- Run ID: `b6ad2a0f-1b40-49e2-8ce6-28b14f8b2df8`
- Matrix: `l4-minimax-m3-canonicalized-v2.json`
- Condition: `l4-minimax-m3-canonicalized-development-v1`
- Code revision: `2e1ff851911cd4c0a26f0cd4d4d69dee48bc44aa`
- Run Configuration: `fbb8bda9b3746f203b1633f65c9810cebe95567e3fb7798ce2323b50616a149b`
- Artifact SHA256: `05737058cd87f45dd28a39a9a61b538b4be37f02484214106db8ea85fb4441dd`
- `60 / 60` scored, `0` execution failures.

Batch + Parallel replication:

- Run ID: `d76ac5ca-22a3-4c67-acf3-c33bba68f0d5`
- Matrix: `l4-minimax-m3-batch-parallel-canonicalized-v1.json`
- Condition: `l4-minimax-m3-batch-parallel-canonicalized-development-v1`
- Code revision: `2e1ff851911cd4c0a26f0cd4d4d69dee48bc44aa`
- Run Configuration: `a4329af87213eb9db245f135095e97959615b61ff882849c7e9543079819c8b9`
- Artifact SHA256: `cf4c16f8e0ac0844c2bc1a2c337dcdb6a3e1c167fdc12806eb8a06b17560ab3c`
- `60 / 60` scored, `0` execution failures.

Both manifests record `git_dirty=true`. The known workspace state immediately before this replication work had no tracked modifications and contained the unrelated untracked `.worktrees/` entry that had already explained the initial dirty bit. Both replication runs use the same recorded code revision and dirty-state class; the artifacts are retained rather than repeated merely to flip that metadata flag.

### 5.2 Replication quality

| Metric | Single / Sequential | Batch + Parallel | Delta |
| --- | ---: | ---: | ---: |
| Execution Coverage | 100.00% | 100.00% | 0.00 pp |
| Failure Type Exact Match | 71.67% | **75.00%** | **+3.33 pp** |
| Evidence Hit Rate | **74.64%** | 73.50% | -1.14 pp |
| Required Fields Completeness | 93.33% | **98.13%** | **+4.79 pp** |
| Protocol Validity | **93.33%** | 91.67% | -1.67 pp |

The initial `-8.33 pp` taxonomy delta did **not** reproduce; its direction reversed. The new single/sequential baseline itself moved from the earlier fresh canonicalized `81.67%` taxonomy result to `71.67%`, directly demonstrating that hosted regeneration variance is large enough to dominate one 20×3 comparison.

A paired Case-level bootstrap over the 20 common Cases gives broad 95% diagnostic intervals for Batch minus single/sequential:

| Metric | Observed delta | 95% paired Case bootstrap interval |
| --- | ---: | ---: |
| Failure Type Exact | +3.33 pp | [-8.33, +15.00] pp |
| Evidence Hit | -1.14 pp | [-9.56, +7.47] pp |
| Required Fields | +4.79 pp | [-1.67, +11.46] pp |
| Protocol Validity | -1.67 pp | [-8.33, +5.00] pp |

These intervals are diagnostic rather than benchmark significance claims, but all cross zero. Current evidence therefore does not demonstrate a reproducible material quality regression from batching.

### 5.3 Replication protocol audit

Single/sequential reference:

- protocol-valid: `56 / 60`;
- protocol-invalid: `4 / 60`;
- all four invalid Samples were `invalid_report_type`.

Batch + Parallel:

- protocol-valid: `55 / 60`;
- protocol-invalid: `5 / 60`;
- validation errors: `unknown_evidence_id=4` occurrences across 3 Samples, `missing_required_field=1`, `invalid_report_type=1`.

The initial Batch run's concentrated `8 × invalid_report_type` pattern therefore did not reproduce. Diagnostic-only inspection found the expected `failure_type` present in all four invalid single/sequential visible outputs and in four of five invalid Batch visible outputs. Formal scores remain unchanged; this inspection only distinguishes output realization from diagnosis semantics.

## 6. Replicated Runtime efficiency

The second block reproduces the mechanism strongly and without the initial 600-second timeout confound.

| Operational observation | Single / Sequential | Batch + Parallel | Change |
| --- | ---: | ---: | ---: |
| Successful Model Decisions | `877` | `571` | **-34.89%** |
| Tool-use decisions | `817` | `511` | **-37.45%** |
| ToolCalls executed/started | `809` | `775` | -4.20% |
| Raw input tokens | `23,448,236` | `15,696,354` | **-33.06%** |
| Output tokens | `301,898` | `286,089` | -5.24% |
| Total tokens | `23,750,134` | `15,982,443` | **-32.71%** |
| Run wall time | `978.27 s` | `806.69 s` | **-17.54%** |
| Sample mean duration | `77.92 s` | `57.19 s` | **-26.60%** |
| Sample p50 duration | `63.13 s` | `45.83 s` | **-27.42%** |
| Sample p95 duration | `184.51 s` | `132.73 s` | **-28.07%** |

The baseline's `817` tool-use decisions include `809` executed single-call decisions plus `8` multi-call decisions whose `20` ToolCall IDs were rejected before execution. The Batch treatment had no `multiple_tool_calls_rejected` events.

Batch behavior in the replication:

- tool-using decisions: `511`;
- multi-call decisions: `228` (`44.62%` of tool-using decisions);
- Samples with at least one multi-call decision: `49 / 60`;
- batch-size distribution: `1×283`, `2×199`, `3×24`, `4×3`, `5×2`;
- no arbitrary call-count cap was needed;
- expected Agent-visible errors remained isolated (`schema_invalid_arguments=9`, `path_not_found=1`);
- no provider retry or Sample-level execution failure occurred.

The key mechanism is not simply "investigate less": executed ToolCalls changed only `809 -> 775` (-4.20%), while Model Decisions changed `877 -> 571` (-34.89%). The model performed nearly the same amount of evidence acquisition while grouping many independent calls into fewer decision turns.

## 7. Provider usage and billing boundary

Replication provider usage:

| Usage | Single / Sequential | Batch + Parallel |
| --- | ---: | ---: |
| Input tokens | `23,448,236` | `15,696,354` |
| Cached prompt tokens | `21,618,995` | `13,775,981` |
| Cache ratio | `92.20%` | `87.77%` |
| Non-cached prompt tokens | `1,829,241` | `1,920,373` |
| Output tokens | `301,898` | `286,089` |
| Total tokens | `23,750,134` | `15,982,443` |

Raw token traffic fell materially, but non-cached prompt tokens increased about `4.98%` because cache behavior differed. Therefore the experiment does **not** claim a 33% billing-cost reduction. It establishes lower Model Decision count, lower raw token traffic, and lower observed latency; billable cost must be calculated from the provider's cache-aware pricing contract separately.

## 8. Two-block interpretation

The two fresh comparisons now show:

| Metric delta, Batch minus reference | Initial comparison | Replication |
| --- | ---: | ---: |
| Failure Type Exact | -8.33 pp | +3.33 pp |
| Evidence Hit | -3.64 pp | -1.14 pp |
| Required Fields | -12.91 pp | +4.79 pp |
| Protocol Validity | -6.67 pp | -1.67 pp |
| Model Decisions | `798 -> 547` (-31.45%) | `877 -> 571` (-34.89%) |

Quality differences are unstable and can reverse direction. Efficiency improvement is stable and similar in magnitude across independent fresh generations.

Evidence Hit and Protocol Validity are slightly lower for Batch in both comparisons, but the replication deltas are small, Case-level uncertainty is broad, and the protocol failure modes themselves did not reproduce. Record this as a weak residual signal to watch in future runs, not as a demonstrated regression.

## 9. Decision

The implementation qualification and replication **pass**.

Current evidence supports the following conclusions:

- same-decision parallel ToolCalls execute correctly with barrier/source-order semantics;
- the model uses batching materially without prompt pressure;
- historical reject-all multi-call friction disappears;
- expected per-call errors remain isolated;
- no artificial ordinary ToolCall count cap is justified;
- Model Decisions fall by roughly 31–35% across the two fresh Batch runs;
- the clean replication reduces wall time by 17.5% and median/p95 Sample latency by about 27–28%;
- the initial formal quality drop is not reproducible and is best treated as hosted generation / output-realization variance rather than evidence of a Batch-induced diagnosis collapse;
- no reproducible material quality regression has been demonstrated.

Therefore Batch + Parallel becomes the **recommended forward Tool Policy for new L4 evaluations and Runtime evolution**. This recommendation does not retroactively rewrite the historical L4 V1 baseline, its matrices, fingerprints, or milestone results, and it does not require silently changing direct-code defaults outside an explicit Treatment identity.

```text
historical reference
single + sequential + reject-all

recommended forward L4 treatment
batch + parallel + independent-call handling
```

Do not respond to these results by adding arbitrary batch caps, forced-batching prompt language, output repair, scheduler heuristics, or a new Runtime rung.

The Batch experiment is complete. The next large capability direction is executable repair / sandboxed remediation, while retrieval, compaction, planner/verifier, memory, and multi-agent work remain evidence-gated rather than automatically added.
