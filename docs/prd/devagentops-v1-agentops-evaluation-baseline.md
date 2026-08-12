# PRD: DevAgentOps V1 AgentOps Evaluation Baseline

## Problem Statement

The user needs DevAgentOps V1 to be more than a one-off agent demo. They need a developer-focused CI/Test Failure Triage AgentOps system where triage runs are traceable, evaluable, repeatable, and governable, so runtime changes, prompt changes, retrieval changes, model changes, and tool policy changes can be compared fairly.

Without this V1 baseline, the project cannot answer whether a self-built ReAct runtime improves over a fixed pipeline baseline, whether retrieval helps, whether a badcase was fixed without causing regressions, or whether a future framework runtime, MCP integration, skill package, sandbox upgrade, or multi-agent runtime is actually better.

## Solution

Build the V1 AgentOps evaluation baseline for DevAgentOps.

The system will provide a fixed pipeline baseline and a self-built single-agent ReAct runtime, both evaluated through the same formal evaluation pipeline. Formal evaluation will run repository-defined evaluation matrix conditions against immutable evaluation suite versions, validate component and case fingerprints, produce run traces and structured triage reports, score metric vectors, update metric-specific leaderboards, and create badcases for review.

V1 will keep scope disciplined: it will support local offline case packages, a versioned tool registry, lightweight hybrid retrieval, structured evidence references, tool policy sandboxing, SQLite persistence, CLI-driven evaluation, ignored report artifacts, and a read-and-review dashboard. It will defer real MCP servers, full skill packaging, multi-agent triage, cross-run agent memory, OS-level sandboxing, interactive human confirmation, external CI integrations, and Langfuse-backed evaluation.

## User Stories

1. As a project builder, I want a fixed pipeline baseline, so that I can compare agentic runtimes against a stable non-agentic workflow.
2. As a project builder, I want a self-built ReAct runtime, so that I can demonstrate core agent loop control, tool use, trace capture, and report submission.
3. As a project builder, I want runtime variants to be explicit, so that V1, future framework runtimes, and future multi-agent runtimes can be compared without copying the whole project.
4. As a project builder, I want an evaluation matrix, so that formal evaluation runs are selected from a controlled set of anchor, ablation, and candidate conditions.
5. As a project builder, I want matrix defaults, so that common evaluation method, suite, model, and budget settings are not duplicated across conditions.
6. As a project builder, I want one-level condition extension, so that ablation conditions can clearly show which variable changed.
7. As a project builder, I want every formal run to store its effective evaluation condition, so that historical runs remain understandable even if matrix files change later.
8. As a project builder, I want condition fingerprints, so that the system can detect when a condition identifier has silently changed meaning.
9. As a project builder, I want formal leaderboards to compare only matching evaluation method, suite, model configuration, and condition fingerprint contexts, so that rankings are fair.
10. As a project builder, I want model changes to be tested as ablations, so that model capability is not confused with runtime or retrieval quality.
11. As a project builder, I want formal evaluation to use low-randomness model settings, so that comparison noise is reduced.
12. As a project builder, I want repeated runs to be available for selected conditions, so that I can estimate stability without multiplying cost for every condition.
13. As a project builder, I want canonical runs separated from stability samples, so that ordinary leaderboards are not silently averaged.
14. As a project builder, I want run manifests, so that each run records code revision, component versions, component fingerprints, model configuration, and effective condition.
15. As a project builder, I want a repository component registry, so that frozen prompts, tool manifests, retriever configs, sandbox policies, and MCP server sets can be validated.
16. As a project builder, I want draft components and frozen components to be separate, so that local iteration stays fast while formal evaluation stays reproducible.
17. As a project builder, I want component fingerprints based on canonical behavior-affecting manifest fields, so that formatting and notes do not create false version changes.
18. As a project builder, I want formal evaluation to fail fast on component version pollution, so that leaderboard results are not produced from mutated frozen versions.
19. As a project builder, I want a small balanced V1 evaluation suite, so that the first implementation can cover core failure types without building a large benchmark first.
20. As a project builder, I want immutable evaluation suite versions, so that case set, expected answers, and case weights cannot change underneath historical results.
21. As a project builder, I want explicit suite manifests, so that formal suites are not changed by draft cases or directory scanning.
22. As a project builder, I want case fingerprints and suite fingerprints, so that evaluation data drift can be detected before formal runs.
23. As a project builder, I want Offline Case Schema V2 packages to separate Physical Artifacts, Canonical Evidence coordinates, and trusted Evaluator artifacts, so that formal evaluation is reproducible without duplicating or mixing source facts and ground truth.
24. As a project builder, I want every offline case to record provenance and sanitization status, so that the dataset is safe to inspect, publish, and demo.
25. As a project builder, I want eval doctor, so that matrix, component, suite, case, fingerprint, and leakage problems are caught before model cost is incurred.
26. As a developer running formal evaluation, I want the eval runner to run eval doctor first, so that invalid inputs cannot produce leaderboard or badcase results.
27. As a developer debugging behavior, I want case subset debug runs, so that I can iterate on a few cases or previous badcases without running the full suite.
28. As a developer debugging behavior, I want debug runs to show quality gate previews, so that I can estimate readiness before formal evaluation.
29. As a developer debugging behavior, I want debug results excluded from leaderboards, so that exploratory runs do not pollute formal comparisons.
30. As a reviewer, I want run traces with structured trace events, so that I can inspect what the triage agent did without reading raw logs or hidden chain-of-thought.
31. As a reviewer, I want model call metadata in traces, so that I can understand token usage, latency, finish reasons, visible outputs, and tool calls.
32. As a reviewer, I want tool call events in traces, so that I can inspect selected tools, arguments, observations, and policy outcomes.
33. As a reviewer, I want final reports to be structured, so that report completeness, failure type accuracy, and evidence use can be validated consistently.
34. As a reviewer, I want structured reports to cite stable evidence identifiers, so that evidence claims are traceable.
35. As a reviewer, I want invalid evidence references to fail validation, so that hallucinated citations cannot pass evidence scoring.
36. As a reviewer, I want retrieval evidence hits separated from report evidence hits, so that I can tell whether a failure came from search or report synthesis.
37. As a reviewer, I want Evidence Ground Truth to distinguish required key evidence from optional evidence separately from the Expected Answer, so that reports are judged on essential support without mixing evidence selection into Diagnosis Ground Truth.
38. As a reviewer, I want expected answers to allow reviewed acceptable failure types for ambiguous cases, so that classification scoring is fair without inflating exact accuracy.
39. As a reviewer, I want metric vectors instead of one composite score, so that trade-offs between classification, evidence, completeness, and tool path behavior remain visible.
40. As a reviewer, I want per-failure-type score breakdowns, so that weak spots such as flaky failures or dependency failures are not hidden by aggregate metrics.
41. As a reviewer, I want quality metrics separated from operational metrics, so that low cost does not compensate for poor triage quality.
42. As a reviewer, I want quality gates to be formal qualification statuses, so that low-quality runs still produce useful reports and badcases.
43. As a reviewer, I want metric-specific leaderboards, so that I can rank conditions by the quality dimension I am investigating.
44. As a reviewer, I want operational metrics such as cost, latency, token usage, step count, and tool call count, so that I can evaluate efficiency after quality is acceptable.
45. As a reviewer, I want badcases derived from formal evaluation, so that regression analysis is based on reproducible conditions.
46. As a reviewer, I want badcase reasons to be structured with primary and secondary reasons, so that improvement work can be prioritized.
47. As a reviewer, I want scorer-suggested badcase reasons and human-reviewed reasons stored separately, so that automation can be useful without replacing trusted review.
48. As a reviewer, I want minimal badcase review in the dashboard, so that I can inspect traces, reports, expected answers, reasons, and reviewer notes.
49. As a reviewer, I want badcase carryover, so that I can see resolved badcases, persistent badcases, and new regressions across condition versions.
50. As a safety reviewer, I want mutation actions forbidden for V1 triage, so that diagnostic workflows do not edit code, rerun CI, open PRs, or deploy.
51. As a safety reviewer, I want tool policy sandboxing enforced before execution and checked after execution, so that governance violations are both prevented and visible.
52. As a safety reviewer, I want submit report classified as report-write, so that it is distinguished from read-only inspection and external mutation.
53. As a dashboard user, I want to view traces, reports, leaderboards, badcases, and badcase review, so that I can inspect AgentOps results without running jobs from the UI.
54. As a CLI user, I want formal evaluation driven by commands, so that evaluations are scriptable and reproducible.
55. As a CLI user, I want generated evaluation reports written to ignored artifacts by default, so that local runs do not create noisy source changes.
56. As a portfolio builder, I want optional milestone report export, so that selected formal evaluation results can be turned into shareable documentation.
57. As a future implementer, I want MCP, skill packages, multi-agent triage, memory, OS sandboxing, and Langfuse integration represented as future variants or ablations, so that V1 does not block later platform growth.
58. As an evaluation reviewer, I want an Oracle Evidence Diagnostic Condition, so that I can estimate whether a fixed model can diagnose a Case after ordinary evidence discovery difficulty is removed.
59. As an evaluation reviewer, I want Oracle and Agent runs paired only when Suite, model, diagnosis prompt, report contract, scorer, inference settings, and other declared controls match, so that evidence delivery remains the intended intervention.
60. As an evaluation reviewer, I want Agent-System Realization Gap reported as per-Case and per-Failure-Type metric differences rather than one composite score, so that Agent-system opportunities remain diagnosable.
61. As a Case curator, I want evaluator-only `required-evidence.json` to identify a Human-reviewed Minimal Sufficient Evidence Set that contains the facts needed for the Expected Diagnosis without encoding the answer, so that both ordinary evidence scoring and Oracle diagnosis remain trustworthy.
62. As an evaluation reviewer, I want every Formal Case to define a frozen bounded-but-realistic Evidence Universe, so that normal conditions must localize evidence instead of receiving a curator-minimized answer corpus.
63. As a runtime evaluator, I want Physical Artifacts deterministically mapped to answer-neutral Canonical Evidence Units, so that retrieval, tools, traces, reports, scorers, and Oracle construction share stable coordinates.
64. As an evaluation reviewer, I want each ladder condition and the orthogonal Oracle intervention to use an explicit Evidence Acquisition Condition over the same underlying Case, so that evidence access remains a controlled experimental variable.
65. As a Case curator, I want the normal Agent-visible corpus to be materially broader than the hidden Required Evidence subset and contain only authentic natural distractors, so that evidence localization is measured without synthetic-noise difficulty.
66. As a Case curator, I want the raw log and bounded exact-revision repository snapshot to be the only Physical Artifacts in a Formal Case V2 Evidence Universe, so that Project Knowledge can be evaluated independently instead of being silently curated into each Case.
67. As an evaluation reviewer, I want Canonical Evidence Units to reference Physical Artifact source spans with resolved content hashes, so that stable coordinates cannot drift into a second editable copy of the evidence.
68. As an evaluation reviewer, I want Formal Case construction and freezing to wait for the Schema V2 implementation, so that the 20-Case suite is not scaled on a data contract already known to be insufficient.
69. As a runtime evaluator, I want an L0-L5+ capability-attribution ladder, so that model reasoning, fixed orchestration, evidence acquisition, and adaptive Agent control can be compared without assuming they arrive as one indivisible ReAct feature.
70. As a product owner, I want L1 full-context one-shot, L2 fixed model workflow, and L3 static retrieval classified as diagnostic/comparison conditions, so that V1 Product Runtime remains limited to Fixed Pipeline and self-built ReAct.
71. As an evaluation reviewer, I want L1 full-context runs to reject silent truncation as valid full-context results, so that context-budget pressure cannot create a mislabeled comparison.
72. As a runtime designer, I want L4 self-built ReAct to be the first Agentic Runtime and the start of the Agent Runtime kernel lineage, so that later capabilities evolve from an explicit adaptive-control boundary.
73. As a runtime designer, I want Pi treated only as a reference architecture, so that mature loop and interface patterns can inform formal ReAct design without becoming a dependency, compatibility target, or source of DevAgentOps semantics.

## Implementation Decisions

- Build V1 around two Product Runtime variants: a fixed pipeline baseline and a self-built single-agent ReAct runtime. Preserve the shipped `runtime_variant="pipeline_baseline"` identity; `deterministic_pipeline` is its L0 capability label, not a historical rename.
- Use the L0-L5+ Runtime Capability Ladder for capability attribution, not as a mandatory implementation order. Treat L1 full-context one-shot, L2 fixed model workflow, and L3 static retrieval as diagnostic/comparison conditions; L4 self-built ReAct is the first Agentic Runtime and Agent Runtime kernel-lineage starting point. Do not freeze whether L3 must be implemented before L4.
- For L1, require the complete Agent-visible Evidence Universe and prohibit silent truncation from retaining full-context identity. Defer the explicit over-budget mechanism to the L1 implementation design.
- Define evaluation matrix loading as the top-level formal evaluation configuration boundary.
- Support matrix defaults and one-level condition extension, then resolve every condition into a complete effective condition before execution.
- Compute and persist condition fingerprints from effective conditions.
- Require direct leaderboard comparison to use the same evaluation method version, evaluation suite version, model configuration, and condition fingerprint.
- Treat repeated runs as explicit matrix configuration, with one canonical run and optional stability samples.
- Persist run manifests with code revision, effective condition, component versions, component fingerprints, model configuration, tool call protocol, report schema version, and relevant fingerprints.
- Build a repository-managed component registry for frozen behavior-affecting components.
- Separate draft components from frozen components; formal evaluation may reference only frozen components.
- Implement component freezing as manifest validation, canonical fingerprint computation, and registry insertion.
- Validate component manifests at freeze time and again before formal evaluation.
- Record model configuration in conditions and run manifests, but keep it outside the component registry.
- Implement a V1 offline evaluation suite using explicit suite manifests and roughly 20 balanced cases across the core failure types.
- Require Offline Case Schema V2 before Issue #15 constructs and freezes the Formal 20-Case Suite. Separate each package into `physical-artifacts/`, `canonical-evidence/`, and evaluator-only `evaluator/` layers; Issue #22 now implements this V2-only loader contract and retires Schema V1 loading.
- Treat suite versions, case packages, physical artifacts, canonical coordinates, evaluator ground truth, and relevant fingerprints as immutable for formal comparison.
- Require each Formal Case to define an authentic, frozen, offline, bounded-but-realistic Evidence Universe containing only its complete or naturally bounded raw log and bounded exact-revision repository snapshot. Preserve natural neighboring information and natural distractors; do not reduce the corpus to the curator-known answer region or add synthetic irrelevant noise solely to create difficulty.
- Keep Project Knowledge outside the current Formal Case V2 Evidence Universe. It remains a general runtime capability and a future independent retrieval/ablation input, not a required Case artifact.
- Treat the Investigation Workspace as the runtime-facing view of the Evidence Universe. Case construction defines what exists; an Evidence Acquisition Condition defines how Fixed Pipeline, L1/L2/L3 diagnostics, ReAct, or Oracle may observe it.
- Require `physical-artifacts/repository-manifest.json` to declare the exact repository revision and every bounded repository member with normalized path, content hash, and size. Files outside the manifest are outside the Case Universe.
- Deterministically map Physical Artifacts to source-faithful, answer-neutral Canonical Evidence Units. Each unit records its stable ID, source artifact/path, source span, and resolved content hash rather than storing an independently editable content copy. Do not allow arbitrary per-Case algorithms/windows or freeze an uncalibrated universal parameter. After `Canonicalization Profile v1` is Human-frozen, every Formal Case must use the same algorithm and parameters for the same artifact class; repository file count and authentic corpus bounds may still vary by Case.
- Require case provenance and sanitization metadata before a case can enter formal evaluation.
- Implement eval doctor as the preflight integrity checker for formal evaluation.
- Make the formal eval runner call eval doctor before executing any agent or scorer work.
- Implement debug run and case subset debug flows that can compute metric previews without updating formal leaderboards.
- Implement structured triage report validation with required fields, enum validation, non-empty required content, confidence bounds, minimal action specificity, and valid evidence references.
- Version the structured triage report schema as an evaluation and product contract, not as a component registry item.
- Define stable evidence identifiers in case packages and retrieval corpora.
- Allow derived evidence only when it preserves provenance to stable evidence identifiers or source spans.
- Score evidence hit rate as final report citation of expected required evidence.
- Define Retrieval Evidence Hit as trace-backed proof that a runtime observed the necessary facts represented by Required Evidence, and Report Evidence Hit as the final report's valid use/citation of them. Runtime observations first record physical spans and their overlapping Canonical IDs; mere partial overlap must not automatically count as a full hit. Freeze the V1 attribution rule during Canonicalization Profile calibration and report Retrieval/Report hits separately to distinguish not found, found but unused, and found and cited.
- Store Required/Optional Evidence IDs only in evaluator-only `required-evidence.json` as Evidence Ground Truth. Store primary/acceptable failure types and other diagnosis-scoring fields in `expected-answer.json` as Diagnosis Ground Truth.
- Require Human review to treat Required Key Evidence as an inclusion-minimal sufficient set of source-faithful facts for deriving the Expected Diagnosis; Required Evidence must not contain evaluator-authored answer text or reasoning.
- Keep `required_evidence_ids` and all Required/Optional labels hidden from normal conditions. A normal adaptive Agent must not receive the curator-selected Required Evidence set or every Canonical Evidence Unit as an answer menu at episode start; its visible corpus should be materially broader than the required subset. L1 may serialize its complete Agent-visible Universe as an explicit diagnostic intervention, but still cannot access evaluator-only artifacts.
- Define Fixed Pipeline as deterministic execution without a model or autonomous loop; L1 as one fixed model call over the complete Agent-visible Universe; L2 as program-controlled fixed multi-stage model orchestration; L3 as static Retrieval over independently versioned Runtime chunks; ReAct as adaptive multi-step investigation of the Workspace; and Oracle as the ADR 0124 orthogonal diagnostic bypass. Canonical Units are measurement/identity/citation coordinates, not mandatory Retrieval chunks. Not every condition must expose identical search/open capabilities because evidence acquisition is the intervention.
- Define Oracle Evidence as a future diagnostic evidence-delivery condition, not a third V1 Runtime Variant. Derive its runtime input deterministically from reviewed Required Evidence IDs through Canonical Evidence coordinates to Physical Artifacts; do not freeze a separate `oracle-evidence.json` or copied pack. Supply only stable IDs plus resolved source content while withholding Evidence Ground Truth, Expected Answer, Failure Type labels, answer text, tool paths, scorer labels, and curator reasoning.
- Treat the existing five Batch-1 Schema V1 packages only as calibration drafts and do not construct further Cases on Schema V1. B04 has passed Schema V2 Human Review; calibrate and Human-freeze the shared `Canonicalization Profile v1` before expanding Formal Case construction.
- Report Agent-System Realization Gap as paired differences for each applicable higher-is-better diagnosis metric, by Case and Failure Type. Do not mix acquisition-dependent or operational metrics into a composite capability score.
- Score tool path validity by tool categories and evidence-gathering behavior rather than exact micro-trajectory.
- Treat forbidden mutation actions as hard failures for tool path validity.
- Implement V1 tool policy sandboxing as tool allowlists, risk levels, and human confirmation metadata, without OS-level isolation.
- Classify tools as read-only, report-write, or mutation.
- Default to provider-native tool calling when the configured OpenAI-compatible provider supports it, with strict JSON action fallback available for compatibility.
- Capture structured run traces with lifecycle events, model call metadata, tool calls, observations, selected evidence, report submission, evaluation, and failures.
- Do not store full hidden chain-of-thought.
- Store formal evaluation data in SQLite and write human-readable and machine-readable report artifacts to ignored generated output.
- Keep the dashboard read-and-review focused for V1; do not trigger formal or debug runs from the dashboard.
- Provide views for traces, reports, metric-specific leaderboards, badcases, and minimal badcase review.
- Defer real MCP server integration, full skill packaging, multi-agent triage, cross-run agent memory, OS-level sandboxing, interactive human confirmation, external CI provider integration, auth/RBAC, Langfuse-backed evaluation, and composite scoring.

## Testing Decisions

- Use CLI-level tests as the highest seam for formal evaluation behavior. A good test invokes the evaluation commands against fixture matrix and case data, then asserts observable outputs such as validation results, persisted run records, generated reports, and leaderboard updates.
- Use eval doctor tests as the highest seam for configuration integrity. A good test feeds invalid matrices, polluted fingerprints, missing provenance, missing sanitization, unknown schema versions, and forbidden retrieval sources, then asserts clear validation failures before any model call.
- Use fake model providers and fake tool implementations for runtime tests, so tests validate runtime orchestration, tool call handling, trace emission, and report submission without depending on live LLM behavior.
- Use scorer contract tests against fixture reports, Evidence Ground Truth, and Expected Answers. A good test asserts quality metric outputs, acceptable failure type handling, required versus optional evidence behavior, invalid evidence reference handling, and badcase reason generation.
- Use future Oracle contract tests to assert exact frozen-evidence resolution, non-leakage of every evaluator-only field, pairing-key validation, condition/run identity capture, metric-specific gaps, PASS-quadrant interpretation, and variance separation with deterministic fake providers.
- Use component registry tests to validate draft versus frozen behavior, manifest schema validation, canonical fingerprint stability, version pollution detection, and freeze command behavior.
- Use Schema V2 suite/case loader and `eval doctor` tests to validate explicit suite manifests, physical-artifact membership and hashes, exact repository revision, canonical source-span resolution and hashes, evaluator-artifact separation, case/suite fingerprints, provenance, sanitization, and Agent-boundary leakage prevention. Preserve Schema V1 fixture compatibility only where the implementation Issue explicitly requires it; semantic relevance, answer-neutral segmentation, and absence of manufactured distractors remain Human Review obligations.
- Use run manifest tests to assert that resolved effective conditions, component fingerprints, condition fingerprints, model configuration, report schema version, and code revision are captured.
- Use trace tests to assert external behavior: trace events are emitted and persisted for run lifecycle, model calls, tool calls, observations, report submission, scoring, and failures.
- Use tool policy tests to assert that forbidden mutation actions are blocked by policy and also scored as invalid if they appear in a trace.
- Use leaderboard tests to assert that only formal evaluation runs can update leaderboards, debug runs are excluded, and direct comparison partitions by evaluation method, suite, model configuration, and condition fingerprint.
- Use badcase tests to assert that formal evaluation failures create structured badcases, suggested and reviewed reasons are stored separately, and carryover identifies resolved, persistent, and new regressions.
- Use dashboard/API tests at the read seam. A good test loads seeded persisted evaluation data and asserts the dashboard/API can retrieve traces, reports, leaderboard rows, badcases, and badcase review data without requiring UI-triggered jobs.
- Avoid tests that assert implementation details such as internal parser helper calls, private class structure, or exact intermediate data layout when CLI/API behavior is sufficient.
- Keep live-provider tests optional and excluded from default local test runs. Formal correctness should be covered by deterministic fake providers and fixture data.

## Out of Scope

- Real MCP server integration.
- Full skill packaging, skill marketplace, skill dependency management, or skill docs bundling.
- Multi-agent triage.
- Cross-run agent memory.
- OS-level sandboxing such as containers, seccomp, or microVMs.
- Interactive blocking human confirmation flow.
- External live CI provider integrations.
- Automated remediation, code edits, rerunning CI, pull request creation, or deployment actions.
- Auth, login, RBAC, and multi-user workflow.
- Langfuse, LangSmith, or other external observability/evaluation backends as the V1 source of truth.
- Composite overall scoring and one global winner leaderboard.
- Dashboard-triggered formal or debug runs.
- Large-scale benchmark construction beyond the initial balanced V1 evaluation suite.
- Semantic leakage detection beyond path and configuration checks.
- Full issue workflow for badcases, including assignment, comment threads, approval states, or permissions.

## Further Notes

- The primary test seams are CLI commands, matrix/suite/component validation, fake-provider runtime execution, scorer contracts, persistence/API reads, and dashboard read views.
- The accepted ADR baseline is the source of architectural truth for this PRD.
- The first implementation slice should start with the evaluation matrix, effective condition resolution, component registry, suite/case artifact loading, and eval doctor, because those define the formal evaluation boundary before model execution.
- V1 should optimize for reproducibility, diagnosability, and honest comparison before cost optimization or feature breadth.
- [`earendil-works/pi`](https://github.com/earendil-works/pi) is the current canonical Pi reference architecture; `badlogic/pi-mono` is historical lineage only. Pi is not a dependency, compatibility target, or semantics source. A concrete reference matrix is deferred to formal ReAct design.
- Oracle Evidence execution and Model-vs-Agent Gap Analysis remain a separate implementation concern after the relevant runner/model seams exist. Issue #15 still owns Formal Suite curation; B04 has passed V2 Human Review, and a shared Canonicalization Profile must be calibrated and frozen before further Formal Case construction.
- Formal Evaluation evidence construction and access semantics are defined in [Formal Evaluation Methodology: Evidence Universe and Access Conditions](../evaluation/formal-evaluation-methodology.md) and [ADR 0126](../adr/0126-offline-case-schema-v2-physical-artifacts-and-canonical-evidence.md). Runtime capability attribution is defined in [Runtime Capability Ladder and Model-backed Diagnostic Conditions](../evaluation/runtime-capability-ladder.md) and [ADR 0127](../adr/0127-staged-runtime-capability-ladder-and-reference-boundary.md). Issue #22 implements the V2 storage/validation/fingerprint/public-boundary contract; it intentionally does not implement migration, Runtime evidence acquisition, Retrieval, Agent, or Oracle enforcement.
