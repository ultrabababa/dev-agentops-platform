# Oracle ↔ L4 Pair Analysis Findings — 2026-08-19

## Overview

This document records the Human / AI review of the first real Oracle ↔ L4 Pair Analyzer output for `triage-suite-v1` using MiniMax-M3.

The Pair Analyzer itself performs only deterministic alignment, aggregation, gap calculation, and evidence packaging. The causal interpretations in this document were made after reviewing the generated `pair-analysis.md` across all 15 detailed-review Cases.

This is a diagnostic analysis milestone. It is not a new Runtime result, not a new scorer, and not a replacement for the frozen historical L1/L2/Oracle/L4 baselines.

The implementation decision evolved after the initial badcase review. The first review framed Canonical Evidence coordinate assistance as a narrow L4-only ablation. Subsequent design review concluded that deterministic final-report Evidence-reference normalization is a shared output-realization responsibility and should be applied consistently to L1, L2, Oracle, and L4 before producing the next current comparison generation. The current decision is recorded below.

## Pair identity

- Oracle run: `388dc6a6-6483-4e11-9b4a-5c935929bd5a`
- L4 run: `dd8ca829-5051-43b6-a0c2-b3c2889acae0`
- Suite: `triage-suite-v1` version `1`
- Model: `MiniMax-M3`
- Gap convention: `Oracle - L4`
- Primary comparison unit: Case aggregate
- Repeat indexes are not treated as paired Oracle/L4 samples

The generated Pair Analyzer output covered all 20 Cases and expanded 15 Cases for detailed review.

## Suite realization gap

| Metric | Oracle | L4 | Gap |
|---|---:|---:|---:|
| Failure Type Exact Match | `0.8500` | `0.8833` | `-0.0333` |
| Evidence Hit Rate | `0.8929` | `0.6551` | `+0.2377` |
| Protocol Validity | `1.0000` | `0.8136` | `+0.1864` |
| Required Fields Completeness | `1.0000` | `0.9667` | `+0.0333` |
| Execution Coverage | `1.0000` | `0.9833` | `+0.0167` |

The suite-level result is therefore not a generic "Oracle is better" outcome.

L4 slightly exceeds Oracle on taxonomy exact match while remaining substantially behind on Evidence Hit and protocol validity. The largest current realization gaps are therefore evidence/report realization rather than raw taxonomy classification.

## Protocol failure concentration

Among the `59` scored L4 Samples:

- protocol-valid Samples: `48`
- protocol-invalid Samples: `11`
- protocol validity: `81.36%`

The invalid Samples break down as:

- `8/11` Samples with one or more `unknown_evidence_id` errors
- `2/11` Samples with `invalid_report_type`
- `1/11` Sample with `duplicate_evidence_reference`

If an idealized deterministic normalization pass removed only the eight unknown-ID failures while changing nothing else, protocol validity would have an upper-bound counterfactual of:

```text
56 / 59 = 94.92%
```

This is not a forecast for a new formal run. It only shows that Canonical Evidence reference failures are large enough to deserve a shared Runtime/output-layer fix rather than being treated as incidental model noise.

## Human / AI badcase findings

The detailed review shows four materially different failure mechanisms. These are review interpretations, not persisted Pair Analyzer labels.

### 1. Canonical coordinate / final-report mapping failures

Several Cases show a clean pattern:

```text
Agent located the relevant physical content
  -> diagnosis was substantially correct
  -> final report invented or malformed a Canonical Evidence ID
  -> protocol validity and/or Evidence Hit collapsed
```

Strong examples:

- `bugswarm-traccar-170287308`
  - all three L4 repeats selected the correct taxonomy and reconstructed the decoder-regex failure;
  - repeat `0` cited the invented log span `log:raw-log:lines-2300-2632` and became protocol-invalid;
  - repeats using valid Canonical IDs achieved full Evidence Hit.

- `bugswarm-apache-struts-190697114`
  - all three repeats correctly diagnosed the `to large` versus `too large` assertion mismatch;
  - repeats `0` and `2` invented non-canonical log spans and became protocol-invalid;
  - the core diagnosis was already correct before the final citation failure.

- `bugswarm-spring-hateoas-232784946`
  - all three repeats correctly identified the Spring 5 / Jackson 2.8.5 incompatibility;
  - all three reports were protocol-invalid: two from unknown Evidence IDs and one from a duplicate citation;
  - this is the strongest concentration of final-report realization loss in one Case.

- `bugswarm-traccar-166900445`
  - two repeats were fully correct;
  - the remaining repeat still identified the placeholder SMTP credential mechanism but cited an invented raw-log coordinate and became protocol-invalid.

- `bugswarm-blueflood-80881330`
  - one repeat was an invalid outer report type;
  - one repeat correctly identified the `metrics` versus `graphite_event` mapping mismatch but invented a repository Evidence ID;
  - the successful repeat shows the diagnosis can be realized under the baseline when the citation is valid.

- `odrepair-dubbo-737f7a7e`
  - L4 reconstructed the stale RpcContext / AsyncContext pollution chain strongly across repeats;
  - one otherwise strong repeat lost protocol validity because it invented a repository coordinate.

These Cases provide direct evidence that part of the Oracle-L4 gap is not evidence acquisition or causal reasoning. It is failure to serialize a physical line-range reference back into the exact frozen Canonical coordinate vocabulary.

### 2. Investigation-depth / evidence-acquisition failures

Other Cases do not support a coordinate-only explanation.

- `bugswarm-retrofit-113047638`
  - L4 repeatedly recognized that `ProtoRequestBodyConverter.convert(null)` was not reached;
  - it generally stopped before reconstructing the full lazy-execution chain through `MethodHandler -> OkHttpCall.createRawCall -> RequestFactory.create -> execute/enqueue`;
  - the missing evidence is primarily investigation depth, not final coordinate mapping.

- `bugswarm-sonar-php-206164136`
  - shallow repeats stopped at the symptom that TESTS measures were not persisted;
  - the strongest repeat continued through `PhpUnitService` / `PhpUnitTestFileReport` into the fixture XML and found that `Monkey.php` was absent from the report paths;
  - the repeat-level improvement tracks deeper investigation rather than a citation-format fix.

These Cases should not be used as evidence that Canonical reference normalization solves the whole realization gap. They point toward later Retrieval / investigation-strategy work.

### 3. Evidence-selection gaps after broadly correct diagnosis

Several Cases show correct or near-correct causal diagnosis with protocol-valid reports, but weaker coverage of the frozen Required Evidence set.

Examples include:

- `github-tan-cli-30459137058`
- `bugswarm-cola-12505170926`
- `idflakies-cukes-http-b483e1a8`

In these Cases, Canonical reference normalization may not recover the Evidence Hit gap because the Runtime cannot select evidence on the model's behalf. The model must still decide which references support its report.

### 4. Genuine causal-reasoning failures

`odrepair-remoting-abf0455a` remains the cleanest reasoning bottleneck.

Oracle and L4 both achieved `0/3` taxonomy exact match. Protocol was valid throughout, and Oracle already supplied the reviewed evidence directly. Neither condition reliably reconstructed the frozen causal chain:

```text
polluter test
  -> invalid regex override during ClassFilter static initialization
  -> class initialization becomes poisoned in the JVM
  -> later victim test observes the failure
```

This Case should not motivate more citation machinery, planner machinery, or extra tools. It demonstrates a reasoning limitation that remains even after relevant evidence is available.

## Adaptive investigation can add real value

The comparison also contains clear negative-gap Cases where L4 outperforms Oracle.

### `github-osquery-issue-7718`

- Oracle taxonomy exact match: `0/3`
- L4 taxonomy exact match: `3/3`
- Evidence Hit: equal at the Case aggregate
- Protocol: fully valid in both conditions

L4 autonomously discovered the startup-readiness race:

```text
test pre-creates pidfile
  -> pidfile existence is used as readiness
  -> readiness check can pass before SIGINT handler installation
  -> SIGINT arrives too early
  -> default signal termination returns -2
```

Oracle received the reviewed evidence but still focused on the visible signal-handler symptom. This is strong evidence that adaptive investigation itself can improve causal reconstruction.

### `odrepair-dubbo-737f7a7e`

L4 also exceeded Oracle on taxonomy aggregate (`2/3` exact versus `1/3`) while recovering the concrete stale thread-local / AsyncContext victim chain in detail.

These Cases argue against replacing L4 investigation with an Oracle-like evidence-delivery shortcut. The next correctness change should preserve each Runtime's existing evidence-acquisition semantics while removing the shared final-reference realization defect.

## Resource-consumption baseline

The preserved milestones also expose a second engineering problem: adaptive L4 investigation is substantially more expensive in Model Decisions, prompt traffic, and wall-clock time than the simpler conditions.

| Condition | Model calls / successful decisions | Prompt tokens | Completion tokens | Total tokens | Full-run wall clock |
|---|---:|---:|---:|---:|---:|
| L1 | `60` | `7,901,430` | `283,392` | `8,184,822` | not recorded as a comparable full-run total |
| L2 | `120` | `15,869,490` | `379,320` | `16,248,810` | approximately `16m25s` |
| Oracle | `60` | `442,140` | `174,538` | `616,678` | `317s` |
| L4 | `802` successful Model Decisions / `807` provider attempts | `24,720,712` | `328,447` | `25,049,159` | approximately `35m01s` |

L2 consumed approximately `1.99x` the total tokens of L1. L4 consumed approximately `3.06x` the total tokens of L1 and `1.54x` the total tokens of L2.

The Oracle numbers are recorded for completeness but must not be interpreted as a Runtime-efficiency ranking. Oracle changes the evidence-delivery condition by providing a much smaller selected-evidence input and is a diagnostic control rather than a capability-ladder Runtime.

For L4, prompt traffic dominates completion traffic because every adaptive Model Decision replays the growing conversation. Provider-reported cached prompt tokens materially reduce the likely billing impact relative to treating every prompt token as an uncached token, but token traffic and Model Decision count remain useful engineering measurements.

The formal L4 run also recorded `26` `multiple_tool_calls_rejected` ToolCall IDs. That is direct evidence that the current single-call Tool Policy sometimes forces avoidable recovery decisions instead of executing a model-proposed batch.

## Updated decision: shared Evidence Reference Canonicalization

The earlier proposal for a narrow L4-only coordinate-assistance ablation is superseded.

The current decision is:

> Deterministic Canonical Evidence Reference Resolution is shared final-report/output infrastructure and should apply consistently to L1, L2, Oracle, and L4.

It is not a new `runtime_variant`. L1, L2, Oracle, and L4 retain their existing Runtime semantics. The shared behavior belongs at the final report-realization boundary, before the existing report validation and scorer.

Conceptually:

```text
Runtime-specific model execution
  -> raw candidate document
  -> shared Evidence Reference Canonicalization
  -> Structured Report validation
  -> frozen scorer
```

### Resolution semantics

For each final `evidence_references` entry:

1. If the reference is already an exact frozen Canonical Evidence ID, preserve it.
2. If the reference is not an exact ID but can be parsed as the same Canonical evidence family plus an explicit line range, deterministically map its overlapping span to the frozen Canonical unit(s).
3. Deduplicate the resolved Canonical references.
4. If no deterministic same-family line-range mapping exists, do not guess, fuzzy-match, or use a model to repair it; leave it unresolved so normal validation can reject it.

The resolver must not inspect or use:

- `required_evidence_ids`;
- Expected Answer;
- evaluator labels or reasoning;
- failure type or root cause;
- semantic similarity or fuzzy path matching;
- Agent trajectory/read-history as an additional repair gate.

The last point is deliberate. Existing conditions already expose or validate Canonical citation vocabulary without requiring a separate proof that every final citation was physically read during the trajectory. Adding a special provenance rule only for repaired references would create a new scoring/grounding contract rather than solving the observed representation defect.

The Runtime is therefore not choosing which evidence the model should cite. It is only normalizing a model-authored line-range representation into the frozen Canonical coordinate representation owned by the evaluation/runtime system.

### Identity boundary

The implementation should be versioned as shared output-realization behavior rather than as an L4-specific Tool Policy, Tool Registry, or Runtime variant.

The exact implementation identity will be frozen during implementation, but the intended boundary is a new shared output-contract generation referenced by all four current conditions. Historical Treatment/Condition fingerprints and milestone artifacts remain unchanged.

The system should preserve enough audit information to distinguish the raw model candidate from the resolved candidate so that normalization behavior remains inspectable.

## Validation and rerun plan

The new shared behavior should be evaluated in two stages.

### Stage A — offline replay of historical outputs

Because canonicalization happens after model generation, replay the preserved historical raw `candidate_document` outputs for L1, L2, Oracle, and L4 through the new resolver and the unchanged frozen scorer.

This provides a zero-model-cost counterfactual:

> Holding every historical model output fixed, how much protocol validity and Evidence Hit are recovered solely by deterministic reference normalization?

This replay is a diagnostic calculation, not a replacement for new formal runs.

### Stage B — new formal comparison generation

After the resolver is implemented and validated, rerun the full current comparison set with the same shared normalization capability:

```text
L1     20 Cases × 3 repeats
L2     20 Cases × 3 repeats
Oracle 20 Cases × 3 repeats
L4     20 Cases × 3 repeats
```

The old milestones remain historical baselines. The newly rerun L1/L2/Oracle/L4 results become the fair current comparison generation because all four conditions share the same final Evidence-reference normalization capability.

The new comparison should report at least:

- execution coverage;
- Failure Type Exact Match;
- Evidence Hit Rate;
- Required Fields Completeness;
- protocol validity;
- unknown/invalid Evidence-reference counts;
- model calls / Model Decisions;
- prompt, completion, and total tokens;
- provider cache-token observations where available;
- wall-clock time.

A useful expected diagnostic pattern is that Oracle changes little because its historical run already had `60/60` protocol-valid reports and zero unknown Evidence-ID references, while L1/L2/L4 may recover varying amounts of Evidence Hit and protocol validity. This is a hypothesis, not a success criterion.

## Separate next optimization: batch + parallel Tool Policy for L4

Evidence Reference Canonicalization and Tool batching solve different problems and should not be bundled into the same implementation/result comparison.

Canonicalization addresses final-report correctness and Evidence realization across all conditions.

Batch + parallel ToolCall execution addresses L4 Agent execution efficiency. The formal L4 run already produced rejected multi-call decisions, so this is evidence-driven Runtime evolution rather than speculative feature work.

The intended later L4-only evolution is:

```text
Tool Policy:
  single + sequential + reject multiple
      -> batch + parallel

runtime_variant:
  self_built_react
      -> unchanged
```

The Runtime-control prompt must evolve with that Tool Policy because the current prompt explicitly instructs zero-or-one ToolCall per Model Decision. The Tool Registry can remain unchanged if the same four read-only investigation tools and per-tool semantics remain unchanged.

The primary efficiency comparison should then be:

```text
new L4 shared-canonicalization baseline
  vs
new L4 shared-canonicalization + batch-parallel Tool Policy
```

Measure:

- Model Decision count;
- rejected multi-call count;
- executed ToolCall count;
- prompt/completion/total tokens;
- wall-clock time;
- taxonomy, Evidence Hit, protocol validity, and execution coverage to detect quality regressions.

Batch support is expected to be the main source of Model-Decision/token savings because it can eliminate reject-and-retry turns and multiple full-context replays. Parallel execution primarily targets latency of already-batched independent read-only tool calls. The actual effect must be measured rather than assumed.

## What remains outside these changes

The Pair Analysis also establishes what should not be mixed into the current work:

- `retrofit` / `sonar-php` style investigation-depth problems belong to later Retrieval or investigation-strategy experiments;
- evidence-selection gaps require separate analysis from coordinate validity;
- `odrepair-remoting-abf0455a` demonstrates a causal-reasoning limitation that reference normalization cannot solve;
- the single `pygithub` HTTP 529 sample remains an execution-reliability observation, not a diagnosis-quality failure;
- planner, reflection, compaction, memory, and multi-agent behavior remain unjustified by the current evidence.

## Conclusion

The Oracle ↔ L4 comparison does not support a single generic explanation for the realization gap.

The observed gap decomposes into at least:

```text
Canonical coordinate / report realization
Investigation depth / evidence acquisition
Evidence selection
Causal reasoning
Operational execution reliability
Execution efficiency / repeated Model Decisions
```

Two actionable engineering problems are now supported by observed data.

First, Canonical Evidence references have a shared representation-normalization defect. The fix should therefore be shared across L1/L2/Oracle/L4, followed by historical offline replay and new formal reruns of all four conditions under the same output-realization contract.

Second, L4 has a separate efficiency problem caused in part by single-call Tool Policy friction and repeated full-context Model Decisions. After the shared canonicalization generation is established, batch + parallel ToolCall execution should be evaluated as an L4-specific Tool Policy evolution.

The current direction is therefore:

```text
preserve all historical milestones
  -> implement shared deterministic Evidence Reference Canonicalization
  -> offline-replay historical L1/L2/Oracle/L4 outputs
  -> rerun L1/L2/Oracle/L4 under one shared output contract
  -> establish the new fair quality + resource baseline
  -> then test L4 batch + parallel Tool Policy separately
  -> move on rather than stacking unrelated Runtime features
```

## Related records

- [Oracle Evidence Diagnostic Condition and Agent-System Realization Gap](../oracle-evidence-diagnostic-condition.md)
- [L1 MiniMax-M3 Full-Suite Milestone](l1-minimax-m3-full-suite-2026-08-14.md)
- [L2 MiniMax-M3 Full-Suite Milestone](l2-minimax-m3-full-suite-2026-08-15.md)
- [Oracle MiniMax-M3 Full-Suite Milestone](oracle-minimax-m3-full-suite-2026-08-15.md)
- [L4 MiniMax-M3 Full-Suite Milestone](l4-minimax-m3-full-suite-2026-08-19.md)
- [Formal Evaluation Methodology](../formal-evaluation-methodology.md)
