# L3 Static Retrieval V1 Formal Milestone — 2026-08-24

> **Status: implementation and live full-Suite qualification complete. L3 Static Retrieval V1 is accepted as a reproducible diagnostic baseline, not as a demonstrated Evidence Hit improvement over L1/L2.** This milestone records the clean MiniMax-M3 `20 Cases × 3 repeats` formal run and a zero-model-cost evaluator-side acquisition analysis. Machine-readable results are preserved in [`l3-static-retrieval-results-2026-08-24.json`](l3-static-retrieval-results-2026-08-24.json).

## 1. Question and boundary

L3 isolates program-controlled static evidence acquisition while retaining a one-shot downstream model path:

```text
L1
complete Physical Evidence Universe -> Model x1 -> Report

L3
deterministic BM25 + multi-query + RRF
    -> bounded selected Physical Evidence
    -> Model x1
    -> Report
```

L3 is a diagnostic/comparison condition, not a Product Runtime and not an adaptive Agent loop. The frozen retriever does not inspect Required Evidence, Expected Answer, previous results, or badcase history.

## 2. Formal identity and gates

- Run ID: `a9d5bce2-d635-4573-baf1-d26c391fedf8`
- Status: `completed`
- Suite quality status: `complete`
- Code revision: `3c07b5488b231d7b78f90ff805feb102b47d1220`
- Git dirty: `false`
- Condition: `l3-minimax-m3-canonicalized-development-v1`
- Runtime variant: `static_retrieval`
- Model/provider: `MiniMax-M3` / `minimax-official`
- Cases/repeats/Samples: `20 × 3 = 60`
- Maximum Case concurrency: `6`
- Request timeout: `600 s`
- Execution retry count: `0`

Fingerprints:

- Suite: `b61f2e3ff85ec77857625a323680b45344fc68523df7cdf70235fa8236c592ed`
- Retriever: `152e7d7a8ec0e7243e673068f50bb396940354c9660dd2ed5405525f40a2c44d`
- Treatment: `7a4b9e9b7fd95639ec7ed3787a8063abfb742172960117a1cda9d58cca39fde5`
- Condition: `a8c58a947e72228fd08e9575626b57e0f16ac76761ff3b8461186653f5f8d115`
- Execution Policy: `c1f3aa8327a858befa9b77a8cc4bce80798c5c98a5125a0c31158ce109225e5b`
- Run Configuration: `9cb560b749f5f20b6ec409e8acb95bf60189b0802f9fd5173a1728aa549d6d56`

Before the live run, the implementation passed:

- component validation for `l3-static-bm25-multi-query-rrf-v1`;
- full repository regression: `397 passed, 2 skipped, 30 subtests passed`;
- full-Suite `eval doctor`;
- a three-Case live smoke run: `3 / 3` scored, `0` failures.

## 3. Formal result

| Metric | L3 result |
| --- | ---: |
| Execution Coverage | **100.00%** |
| Failure Type Exact Match | **88.33%** |
| Report Evidence Hit Rate | **50.67%** |
| Required Fields Completeness | **99.79%** |
| Protocol Validity | **98.33%** |

Operational health:

- `60 / 60` Samples scored;
- `0` execution failures;
- `59 / 60` protocol-valid Samples;
- all `60` provider completions ended with `finish_reason=stop`;
- `0` unknown Evidence IDs and `0` duplicate Evidence References;
- `2` reports were changed by deterministic line-range canonicalization;
- wall-clock time was approximately `5m28s`.

The only protocol-invalid Sample was `idflakies-cukes-http-b483e1a8#repeat-0`, whose report omitted `confidence`. The same Case's other two repeats were valid. This is a model-output realization miss, not a Runtime or retriever failure.

## 4. Evaluator-side retrieval acquisition analysis

The formal scorer measures only final Report Evidence Hit. L3 Trace also preserves each packed span's answer-neutral `overlapping_canonical_evidence_ids`, so the completed artifact permits a zero-model-cost diagnostic after the run:

```text
exposed_required(case)
  = hidden Required Evidence IDs
    intersect
    union(Trace packed-span overlapping Canonical IDs)

retrieval_acquisition_recall(case)
  = |exposed_required(case)| / |required(case)|
```

This analysis is evaluator-side only. Hidden Ground Truth did not affect retrieval, serialization, model input, or scoring.

Results:

| Diagnostic | Case-first result |
| --- | ---: |
| Retrieval acquisition recall | **76.56%** |
| Final Report Evidence Hit | **50.67%** |
| Utilization of acquired Required Evidence | **66.18%** |

Micro recall across the 89 Case-level Required Evidence IDs was `75.28%`; micro final-report hit across three repeats was `46.82%`. Case-first values remain the primary comparison because the Suite uses equal Case weighting.

No final report cited a Required Evidence ID that was absent from its retrieved input. All `20 / 20` Cases also had one stable `runtime_input_sha256` across their three repeats. Therefore:

- acquisition loss is real: roughly one quarter of Required Evidence IDs were not exposed;
- evidence-selection/reporting loss is also real: the model cited only about two thirds of the Required Evidence that was exposed;
- within-Case repeat variation comes from hosted generation/evidence selection, not retrieval nondeterminism.

### 4.1 By Failure Type

| Failure Type | Acquisition Recall | Report Evidence Hit | Acquired-Evidence Utilization | Failure Type Exact | Protocol Validity |
| --- | ---: | ---: | ---: | ---: | ---: |
| `config_or_environment_failure` | 90.00% | 66.11% | 75.00% | 91.67% | 100.00% |
| `dependency_or_install_failure` | 93.75% | 54.31% | 56.39% | 100.00% | 100.00% |
| `lint_or_type_failure` | 66.67% | 47.22% | 75.00% | 91.67% | 100.00% |
| `test_assertion_failure` | 63.49% | 41.40% | 59.13% | 100.00% | 100.00% |
| `timeout_or_flaky_failure` | 68.89% | 44.29% | 65.40% | 58.33% | 91.67% |

### 4.2 Case diagnostics

| Case | Required exposed | Acquisition | Report hit | Taxonomy exact |
| --- | ---: | ---: | ---: | ---: |
| `bugswarm-apache-struts-190697114` | 1 / 3 | 33.33% | 11.11% | 100.00% |
| `bugswarm-retrofit-113047638` | 3 / 7 | 42.86% | 28.57% | 100.00% |
| `bugswarm-byte-buddy-149441998` | 1 / 2 | 50.00% | 33.33% | 100.00% |
| `bugswarm-checkstyle-77722324` | 1 / 2 | 50.00% | 50.00% | 100.00% |
| `odrepair-dubbo-737f7a7e` | 5 / 9 | 55.56% | 33.33% | 100.00% |
| `idflakies-cukes-http-b483e1a8` | 3 / 5 | 60.00% | 40.00% | 100.00% |
| `github-osquery-issue-7718` | 3 / 5 | 60.00% | 46.67% | 0.00% |
| `bugswarm-blueflood-80881330` | 3 / 5 | 60.00% | 53.33% | 100.00% |
| `bugswarm-mypy-237548392` | 2 / 3 | 66.67% | 55.56% | 66.67% |
| `bugswarm-traccar-221926468` | 3 / 4 | 75.00% | 25.00% | 100.00% |
| `bugswarm-sonar-php-206164136` | 7 / 9 | 77.78% | 37.04% | 100.00% |
| `bugswarm-pygithub-36442425251` | 4 / 4 | 100.00% | 50.00% | 100.00% |
| `bugswarm-spring-hateoas-232784946` | 5 / 5 | 100.00% | 53.33% | 100.00% |
| `bugswarm-cola-12505170926` | 6 / 6 | 100.00% | 55.56% | 100.00% |
| `bugswarm-testng-64757057` | 3 / 3 | 100.00% | 55.56% | 100.00% |
| `github-tan-cli-30459137058` | 3 / 3 | 100.00% | 55.56% | 100.00% |
| `odrepair-remoting-abf0455a` | 7 / 7 | 100.00% | 57.14% | 33.33% |
| `bugswarm-nukkit-94403868` | 2 / 2 | 100.00% | 83.33% | 100.00% |
| `bugswarm-traccar-170287308` | 3 / 3 | 100.00% | 88.89% | 100.00% |
| `bugswarm-traccar-166900445` | 2 / 2 | 100.00% | 100.00% | 66.67% |

The low-hit Cases separate into distinct mechanisms. Apache Struts and Retrofit are dominated by acquisition misses. Traccar `221926468`, Sonar PHP, and several 100%-acquisition Cases expose stronger evidence-selection/citation loss. These must not be collapsed into one generic "retriever failure" label.

## 5. Taxonomy badcases

Seven of 60 Samples missed Failure Type Exact Match. Every miss selected `test_assertion_failure`:

- `github-osquery-issue-7718`: `0 / 3` correct; expected `timeout_or_flaky_failure`;
- `odrepair-remoting-abf0455a`: `1 / 3` correct; expected `timeout_or_flaky_failure`;
- `bugswarm-mypy-237548392`: `2 / 3` correct; expected `lint_or_type_failure`;
- `bugswarm-traccar-166900445`: `2 / 3` correct; expected `config_or_environment_failure`.

The common pattern is surface-label attraction: an assertion/test error is selected even when the causal class is flaky/test isolation, type checking, or environment configuration. This is a taxonomy/reasoning calibration issue. It is not evidence that retrieval execution failed.

## 6. Token, latency, and retrieval observations

Provider usage across 60 one-shot completions:

| Observation | Value |
| --- | ---: |
| Input tokens | `1,828,695` |
| Output tokens | `140,388` |
| Total tokens | `1,969,083` |
| Reasoning tokens | `90,645` |
| Mean total tokens / Sample | `32,818` |
| Mean latency | `25.73 s` |
| p95 latency | `54.82 s` |
| Maximum latency | `74.83 s` |

Mean selected evidence per Sample was `8.1` log chunks and `9.4` repository chunks. Packing produced a mean of `9.9` physical spans and `97,794` runtime-input bytes.

These are operational diagnostics, not components of diagnosis quality.

## 7. Canonicalized comparison boundary

| Condition | Execution | Taxonomy | Evidence Hit | Required Fields | Protocol |
| --- | ---: | ---: | ---: | ---: | ---: |
| L1 canonicalized | 98.33% | 80.00% | 52.16% | 99.79% | 96.61% |
| L2 canonicalized | 96.67% | 83.33% | 54.15% | 98.33% | 98.28% |
| **L3 static retrieval** | **100.00%** | **88.33%** | 50.67% | **99.79%** | **98.33%** |
| L4 canonicalized | 100.00% | 81.67% | 71.83% | 99.58% | 93.33% |
| Oracle canonicalized | 100.00% | 83.33% | 85.40% | 96.67% | 96.67% |

L3 has the highest observed taxonomy score in this generation set, but its Report Evidence Hit is `1.49 pp` below L1 and `3.48 pp` below L2, and materially below adaptive L4 and Oracle.

These are fresh hosted generations, not a back-to-back deterministic causal experiment. Regeneration variance was already demonstrated by the canonicalization and Batch milestones. The table supports operational comparison and badcase selection; it does not prove that static retrieval caused the taxonomy uplift or the exact Evidence Hit deltas.

## 8. Decision and next direction

L3 V1 passes implementation and live formal qualification:

- deterministic retrieval and one-shot execution are correct and reproducible;
- formal identity is clean and complete;
- the baseline materially reduces model-visible evidence relative to full-context delivery while preserving 100% execution coverage;
- the Trace is sufficient to attribute acquisition and final-report evidence loss separately.

The quality hypothesis is mixed: static retrieval does not demonstrate a Report Evidence Hit improvement over L1/L2. The result justifies neither silent Top-K/query tuning against this frozen Suite nor immediate addition of embeddings, rerankers, query LLMs, or a vector database.

If retrieval optimization is pursued later, create a separate calibration/development set, freeze a new retriever Treatment, and then evaluate once on the formal Suite. Do not tune `l3-static-bm25-multi-query-rrf-v1` against hidden `triage-suite-v1` Ground Truth.

L3 is now a completed diagnostic baseline. The next large Product Runtime direction remains executable repair / sandboxed remediation; L3 optimization remains evidence-gated and separate.
