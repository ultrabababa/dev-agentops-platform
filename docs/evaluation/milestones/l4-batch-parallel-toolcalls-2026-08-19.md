# L4 Batch + Parallel ToolCalls Milestone — 2026-08-19

> **Status: implementation qualification complete; treatment retained, not promoted to the default L4 baseline.** This milestone records Issue #61 / PR #62, deterministic validation, one fresh `20 Cases × 3 repeats` MiniMax-M3 formal run, runtime-mechanism observations, quality results, and interpretation boundaries. Machine-readable results are preserved in [`l4-batch-parallel-toolcalls-results-2026-08-19.json`](l4-batch-parallel-toolcalls-results-2026-08-19.json).

## 1. Question

Historical and fresh canonicalized L4 traces showed that MiniMax-M3 naturally emitted multiple same-decision ToolCalls even though the frozen baseline Runtime-control prompt and Tool Policy required zero-or-one ToolCall and rejected every call in a multi-call decision.

The experiment asks whether L4 should support a distinct Tool Policy treatment with:

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
- L4 condition/treatment resolution that accepts the historical baseline pair or the candidate pair without rewriting historical component identities;
- focused regression coverage for actual concurrency, order, duplicate calls, per-call expected errors, infrastructure failure, length truncation, step accounting, component identity, and Matrix validation.

Maintainer-side validation passed:

- focused regression: `29 passed`;
- candidate `eval doctor`: PASS;
- full repository regression: `377 passed, 2 skipped, 30 subtests passed`.

## 4. Formal run identity

Candidate formal run:

- Run ID: `010e9a75-8ca8-44b5-8445-d82d188d11f3`
- Status: `completed`
- Suite quality status: `complete`
- Condition: `l4-minimax-m3-batch-parallel-canonicalized-development-v1`
- Code revision: `ae6b756d13471a68c263583533795ef1c2a47231`
- Cases: `20`
- Repeats: `3`
- Planned / scored Samples: `60 / 60`
- Execution failures: `0`
- Maximum cross-Case concurrency: `6`
- Provider request timeout: `600 s`
- Artifact SHA256: `a8e73a66de70788aa7fc59fce881723ef6e4d75d0127767aa0a4da64765fe67d`

Fingerprints:

- Treatment: `c988c570a1e0ed5623933c8c419605cd1f6c2066d2bbe224c6748178391d181e`
- Condition: `d3353424ccfdfeb03772ebf4ff4bd8f1ca6861b051136d2571ef7dea39bae62e`
- Execution Policy: `14e21cd921a1729991f83aa83ce3c9ba8f4603526c3782181255886bbf30461a`
- Run Configuration: `4cdc2facc0f12dd36c09ebd8dde1e982270c50e8fd87a3e3ad28de7776a4dfbc`

### Git state note

The manifest records `git_dirty=true`. Immediately after the run, maintainer verification showed:

```text
git status --short
?? .../.worktrees/

git status --short --untracked-files=no
<no output>
```

Therefore no tracked behavior-affecting file differed from code revision `ae6b756...`; the dirty bit came from an unrelated untracked worktree directory. The run is retained rather than repeated solely to change this metadata bit.

## 5. Runtime mechanism result

The candidate exercised batching heavily without a prompt instruction to prefer it.

| Observation | Candidate |
| --- | ---: |
| Successful Model Decisions | `547` |
| Provider request attempts | `548` |
| Tool-using decisions | `487` |
| ToolCalls started | `787` |
| Multi-call decisions | `257` |
| Multi-call rate among tool decisions | `52.77%` |
| Samples using at least one multi-call decision | `55 / 60` |
| `multiple_tool_calls_rejected` | `0` |

Batch-size distribution:

| ToolCalls in decision | Decisions |
| ---: | ---: |
| 1 | 230 |
| 2 | 221 |
| 3 | 29 |
| 4 | 7 |

No decision exceeded four calls despite the Runtime having no arbitrary ordinary-call cap. Common multi-call combinations were dominated by independent read-only investigation: `read+read`, `grep+read`, `ls+read`, and `grep+grep`.

Expected Agent-visible tool errors remained isolated:

- `schema_invalid_arguments`: `9`
- `path_not_found`: `2`

There was no Sample-level Runtime/tool infrastructure failure.

### Model-decision comparison

The fresh canonicalized single/sequential L4 reference run (`d6fee1ba-ddd2-4ed3-ae2f-625603de5fef`) used `798` successful Model Decisions. Its pre-experiment trace audit found only `14` multi-call decisions because the baseline rejected such outputs.

The candidate used `547` successful Model Decisions:

```text
798 -> 547
-251 decisions
-31.45%
```

This is strong operational evidence that the capability is actually used by the model and removes substantial decision-loop overhead. It is not, by itself, a causal estimate of quality or billing savings.

## 6. Provider usage

Across the `547` successful Model Decisions:

- input tokens: `15,684,626`
- output tokens: `272,805`
- total tokens: `15,957,431`
- cached prompt tokens: `13,328,611`
- cached-input ratio: approximately `84.98%`
- non-cached prompt tokens: `2,356,015`

Relative to the historical pre-canonicalization L4 run, raw token volume is much lower, but cache behavior also differs. Therefore the experiment does **not** claim an equal-percentage billing reduction from total-token reduction.

## 7. Quality result

Formal Suite metrics:

| Metric | Fresh canonicalized L4 reference | Batch + Parallel candidate | Delta |
| --- | ---: | ---: | ---: |
| Execution Coverage | 100.00% | 100.00% | 0.00 pp |
| Failure Type Exact Match | 81.67% | 73.33% | -8.33 pp |
| Evidence Hit Rate | 71.83% | 68.19% | -3.64 pp |
| Required Fields Completeness | 99.58% | 86.67% | -12.91 pp |
| Protocol Validity | 93.33% | 86.67% | -6.67 pp |

These fresh-generation deltas are **not causal estimates of batching**. The earlier canonicalization milestone already established substantial hosted model/provider regeneration variance, including metric movement in Oracle when canonicalization changed zero candidates.

The candidate's eight protocol-invalid Samples are especially important: all eight failed with `invalid_report_type`. None failed because of multi-call rejection, ToolResult ordering, unknown Evidence IDs, parallel execution, or infrastructure failure. Typical invalid outputs wrapped an otherwise report-like JSON payload in explanatory prose, Markdown, or a JSON string.

Among the `52` protocol-valid Samples, simple Sample-level diagnostics were:

- Failure Type Exact: `84.62%`
- Evidence Hit: `78.68%`
- Required Fields: `100.00%`

A diagnostic-only audit of the eight invalid visible outputs found that five still contained the correct `failure_type`. This does not repair or re-score those Samples; it only shows that a large part of the formal aggregate drop is output-realization failure rather than demonstrated diagnosis collapse.

Accordingly, the observed quality regression cannot currently be attributed cleanly to batch execution.

## 8. Long-tail latency

Observed run wall time was approximately `1,378.7 s` (`22m58.7s`). Sample-duration diagnostics:

- p50: `42.44 s`
- p90: `112.90 s`
- p95: `138.15 s`
- maximum: `653.68 s`

The maximum straggler was `odrepair-dubbo-737f7a7e#repeat-2`. At Model Decision step 3, one provider attempt hit the frozen `600 s` timeout (`600,160 ms`). The same logical request then succeeded on retry and the Sample completed.

Therefore the extreme tail is directly explained by a provider timeout, not by parallel tool execution or an observed scheduler deadlock. No batch-size cap, ThreadPool throttling, scheduler rewrite, or timeout-policy change is justified by this run.

## 9. Decision

The implementation qualification **passes**:

- deterministic tests and doctor pass;
- real same-decision parallel calls execute successfully;
- the model naturally uses batching at high frequency under a neutral prompt;
- reject-all multi-call failures disappear;
- expected per-call errors remain isolated;
- barrier/source-order semantics hold without infrastructure failures;
- Model Decisions fall materially in the fresh operational comparison.

However, this run does **not** justify promoting Batch + Parallel to the default canonical L4 baseline yet. Fresh quality metrics are lower, while hosted regeneration variance and `invalid_report_type` failures prevent a clean causal attribution.

The decision is therefore:

```text
merge/support the distinct batch+parallel Tool Policy treatment
    !=
claim that it has already beaten and replaced the single/sequential baseline
```

Do not respond to this run by adding arbitrary batch caps, forced-batching prompt language, output repair, scheduler heuristics, or a new Runtime rung.

The treatment should remain available as a controlled L4 variant. A future default-baseline promotion requires stronger evidence than one fresh hosted comparison. The next large capability direction can remain executable repair / sandbox work unless new evidence motivates another focused ablation.
