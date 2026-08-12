# DevAgentOps

DevAgentOps is a learning and job-seeking project for building a developer-focused agent platform end to end. Its primary domain is CI/Test Failure Triage AgentOps.

## Language

### **DevAgentOps**:

A developer-focused agent platform that combines CI/test failure triage with operational visibility, evaluation, and governance.
_Avoid_: Generic coding assistant, chatbot, Codex clone

### **CI/Test Failure Triage AgentOps**:

The project domain for making automated build and test failure diagnosis traceable, evaluable, repeatable, and governable.
_Avoid_: Generic CI/CD diagnosis, general coding agent, generic AgentOps platform

**Evaluation and Badcase Driven Development (EBDD)**:
An internal development method for improving DevAgentOps by using formal evaluation results, metric vectors, formal badcases, and badcase carryover to decide what to change next. EBDD complements TDD: TDD verifies deterministic software behavior, while EBDD guides agent behavior iteration.
_Avoid_: Product category, external positioning, replacement for CI/Test Failure Triage AgentOps, test-driven development synonym

### **CI/Test Failure Triage**:

A developer workflow for classifying and explaining automated build or test failures using logs, changed code, project knowledge, and historical incidents. It ends with a diagnostic report rather than applying code changes or rerunning CI.
_Avoid_: Broad DevOps automation, generic debugging, automated remediation

**Triage Report**:
A diagnostic explanation of a CI or test failure, including the failure type, supporting evidence, likely root cause, recommended next action, and confidence.
_Avoid_: Auto-fix, pull request, deployment report

**Structured Triage Report**:
A triage report represented with fixed fields so it can be validated, traced, and evaluated consistently.
_Avoid_: Free-form Markdown answer, chat transcript

**Structured Triage Report Schema**:
The versioned contract that defines the fields, required values, and validation rules for structured triage reports.
_Avoid_: Prompt component, tool manifest

**Run Trace**:
The chronological record of a triage run, including agent decisions, model calls, tool calls, report submission, evaluation, and failures.
_Avoid_: Raw application log, chat transcript

**Run Manifest**:
The reproducibility metadata attached to a triage run, including the selected evaluation condition, code revision, and behavior-affecting component versions.
_Avoid_: Run trace, raw log, evaluation report

**Component Fingerprint**:
A stable content identity computed from the canonicalized behavior-affecting manifest of an agent component, used to detect whether the component contract or configuration changed between runs.
_Avoid_: Whole repository hash, file timestamp, display version

**Component Version**:
A human-readable immutable identity for a behavior-affecting agent component used in run manifests and evaluation conditions.
_Avoid_: Mutable config label, release package

**Draft Component**:
A behavior-affecting agent component that may change freely during local experimentation and is not eligible for formal evaluation matrix comparison.
_Avoid_: Frozen component, production version

**Frozen Component**:
A behavior-affecting agent component with a stable component version and fingerprint that may be referenced by formal evaluation conditions.
_Avoid_: Draft component, mutable config

**Component Registry**:
A repository-managed index of frozen component versions, their manifest paths, fingerprints, and review metadata.
_Avoid_: GitHub release, package registry

**Component Manifest Schema**:
The versioned file format contract for a component manifest, defining required fields, behavior-affecting fields, and metadata fields.
_Avoid_: Component version, runtime version

**Trace Event**:
A single structured record inside a run trace that captures what happened at one point in the triage run.
_Avoid_: Log line, debug print

**Trace Stream**:
A live feed of trace events used to show triage progress as the agent investigates a failure case.
_Avoid_: Chat streaming, bidirectional collaboration channel

**Triage Dashboard**:
A focused interface for reviewing offline cases, run traces, structured triage reports, evaluation results, and baseline comparisons.
_Avoid_: Full admin console, generic analytics product

**Offline Case Package**:
A self-contained failure case used for repeatable triage and evaluation without depending on a live CI provider.
_Avoid_: Live CI run, GitHub Actions integration, GitLab CI integration

**Case Provenance**:
The recorded origin, source permissions, and construction history of an offline case package.
_Avoid_: Unattributed sample, copied log fragment

**Case Sanitization**:
The removal or replacement of secrets, personal data, private repository details, and other non-public information from offline case artifacts.
_Avoid_: Raw production dump, unreviewed log sample

**Offline Case Schema**:
The versioned file format contract for an offline case package and its manifest.
_Avoid_: Evaluation suite version, expected answer

**Physical Artifact**:
A source-of-fact file frozen inside an Offline Case Schema V2 package, limited for the current Formal Suite to the raw log and the bounded exact-revision repository snapshot declared by its manifest.
_Avoid_: Canonical evidence copy, evaluator label, current working tree

**Repository Snapshot Manifest**:
The Schema V2 inventory that binds every repository artifact in the bounded Case snapshot to its revision, normalized path, content hash, and size. Files outside the manifest are not part of the Case Evidence Universe.
_Avoid_: Repository index, current checkout, unbounded directory scan

**Case Fingerprint**:
A stable content identity for an offline case package, used to detect whether its physical artifacts, canonical coordinates, evaluator ground truth, or scoring-relevant manifest fields changed.
_Avoid_: Case name, suite fingerprint

**Evidence Universe**:
The authentic, frozen, offline, bounded-but-realistic information space defined by a Formal Case. For Offline Case Schema V2 it consists only of the complete or naturally bounded historical raw log and the bounded exact-revision repository snapshot declared by the Case. It preserves natural neighboring information and distractors instead of being reduced to the curator-known answer region.
_Avoid_: Minimal required evidence set, whole unbounded upstream repository, synthetic noise corpus

**Investigation Workspace**:
The runtime-facing view through which an Evidence Acquisition Condition can observe and investigate a Case's physical log and repository artifacts. Normal adaptive Agents may receive searchable/openable access rather than the complete corpus in initial context; an explicit Full-context One-shot diagnostic may serialize the complete Agent-visible universe without changing evaluator-only boundaries.
_Avoid_: Expected Answer, curator-selected required evidence pack, treating diagnostic delivery as the Workspace definition

**Log Evidence**:
Frozen CI or test output content in the Case Physical Artifacts. Canonical Evidence Units provide stable coordinates for observed/cited source-faithful portions; a Runtime may inspect or retrieve independently chunked physical spans.
_Avoid_: Curator-authored answer summary, prompt context

**Repository Evidence**:
Frozen source, configuration, dependency, test, or build content from the Case's bounded exact-revision repository snapshot. Canonical Evidence Units address this content for identity, measurement, and citation without defining Runtime retrieval chunks.
_Avoid_: Current working tree, unbounded codebase dump, curator-authored answer summary

**Evidence Reference**:
A structured citation in a triage report that points to a specific log, repository, or project-knowledge evidence item.
_Avoid_: Vague evidence summary, unsupported claim

**Stable Evidence ID**:
A deterministic, answer-neutral identifier defined by a Case package's Canonicalization Profile so runtimes, traces, expected answers, reports, and scorers can refer to the same Physical Artifact coordinate.
_Avoid_: Runtime-only evidence label, generated display number, root-cause hint

**Canonical Evidence Unit**:
A deterministic, answer-neutral source-span coordinate over one Physical Artifact, with a resolved content hash used to verify source faithfulness. It is the common coordinate for observation identity, tool results, traces, citations, evidence-attribution signals, and Oracle derivation; it does not duplicate an independently editable evidence copy and is not a mandatory Retrieval chunk. One physical log or repository file may map to multiple units under the suite-shared Human-frozen Canonicalization Profile for that artifact class.
_Avoid_: Duplicated evidence text, physical file count, curator-selected answer evidence, arbitrary per-Case windows, uncalibrated universal parameters, Retrieval index chunk

**Derived Evidence**:
An evidence item created during runtime by retrieval, extraction, or summarization that preserves provenance back to stable evidence or source spans.
_Avoid_: Stable evidence source, unsupported summary

**Project Knowledge**:
The versioned SOPs, runbooks, documentation, and project notes that may be supplied as a general runtime capability or future independent ablation. It is not a Physical Artifact in the current Formal Case Schema V2 Evidence Universe.
_Avoid_: Current Formal Case evidence, chat history, external issue tracker

**Agent Memory**:
Cross-run information made available to an agent from previous interactions, runs, or learned experience.
_Avoid_: Run trace, project knowledge, retrieved evidence

**Triage Knowledge Source**:
A local evidence source available to the triage agent, limited in V1 to log evidence, repository evidence, and project knowledge.
_Avoid_: Live issue tracker, team chat, external wiki

**Log Preprocessing**:
The deterministic, semantics-preserving normalization of raw CI or test output before Canonical coordinates and Runtime-specific retrieval views are derived, without preselecting only the hidden Required Evidence.
_Avoid_: Full-log prompting, curator-performed evidence localization, answer summary

**Retrieval Corpus**:
The versioned Runtime-specific chunks derived from allowed Physical Artifacts or separately controlled Project Knowledge and indexed for retrieval during triage. Retrieved physical spans map back to overlapping Canonical Evidence IDs; the Canonical Unit set itself is not the mandatory corpus chunking.
_Avoid_: Retriever, evaluation suite, expected answer, badcase history

**Triage Tool**:
A read-oriented or report-oriented capability used to inspect a failure case, gather evidence, search project knowledge, and submit a diagnosis.
_Avoid_: Code editing tool, CI mutation tool

**Tool Registry**:
A catalog of available triage tool contracts, including names, descriptions, input schemas, risk metadata, and versioned manifests.
_Avoid_: Skill package, MCP server registry

**Tool Call Protocol**:
The protocol a triage runtime uses with a model to request tool calls, such as provider-native tool calling or validated JSON action fallback.
_Avoid_: Tool registry, tool implementation

**Execution Tool**:
A change-oriented capability that edits code, runs tests, submits pull requests, reruns CI, or otherwise mutates the development workflow.
_Avoid_: Triage tool

**Tool Risk Level**:
A label describing the operational risk of a tool so the system can distinguish read-only inspection from workflow mutation.
_Avoid_: User role, access group

**Human Confirmation**:
An explicit approval step required before a risky agent action proceeds.
_Avoid_: Login, RBAC, automated approval

**Single Triage Agent**:
One agent responsible for gathering evidence, choosing triage tools, and producing a triage report for a failure case.
_Avoid_: Supervisor-agent workflow, role-based multi-agent workflow

**Step Protocol**:
The structured contract a triage runtime uses to represent each agent step, including tool calls, observations, selected evidence, and final report submission.
_Avoid_: Chain-of-thought transcript, free-form ReAct text

**Pipeline Baseline**:
A deterministic, no-model, non-Agentic fixed triage workflow used as the comparison point for Agent Runtime experiments. Its shipped V1 runtime identity is `pipeline_baseline`; `deterministic_pipeline` is the L0 capability name, not a rename.
_Avoid_: Agent runtime, production workflow

**Runtime Variant**:
An independently runnable Product Runtime or workflow implementation that can be compared against other variants using the same evaluation suite. V1 Product Runtime variants are `pipeline_baseline` and `self_built_react`; diagnostic conditions do not automatically become Runtime Variants.
_Avoid_: Project version, copied project directory, every evaluation condition

**Runtime Capability Level**:
A named rung in the L0-L5+ capability-attribution ladder that identifies which class of model reasoning, orchestration, evidence acquisition, or adaptive Agent control is present. Levels guide controlled comparison and do not mandate implementation order.
_Avoid_: Product maturity rank, Matrix schema field, implementation dependency

**Product Runtime**:
An independently supported runtime implementation intended to carry product behavior and evolve as a runtime lineage. V1 Product Runtime is limited to Fixed Pipeline and self-built ReAct.
_Avoid_: Diagnostic condition, Oracle intervention, every ladder rung

**Model-backed Diagnostic Condition**:
A non-Product evaluation condition that uses a model to isolate a capability such as one-shot reasoning, fixed orchestration, or static evidence acquisition.
_Avoid_: Product Runtime, adaptive Agent by default, informal prompt experiment

**Full-context One-shot**:
The L1 non-Agentic diagnostic condition that supplies the complete Agent-visible Evidence Universe through one fixed Prompt and exactly one model call. Silent truncation invalidates the full-context claim; the explicit over-budget outcome is deferred to implementation design.
_Avoid_: Oracle Evidence, partial-context prompt labeled full-context, evaluator artifact access

**Fixed Model Workflow**:
The L2 non-Agentic diagnostic condition in which a program fixes model-call stages, transitions, inputs, and stopping instead of allowing the model to choose an adaptive next action.
_Avoid_: ReAct loop, Product Runtime, unspecified orchestration

**Static Retrieval Diagnostic**:
The L3 non-Agentic evidence-acquisition condition that supplies versioned static retrieval results to a program-controlled model path without adaptive Agent control.
_Avoid_: ReAct tool loop, mandatory predecessor to L4, Canonical Units as forced index chunks

**Agent Runtime Kernel Lineage**:
The self-built adaptive Runtime core that begins at L4 ReAct and is incrementally evolved with later capabilities while retaining explicit state, loop, tool, event, provider, stop, context, evaluation, and safety seams.
_Avoid_: External runtime fork, L1/L2/L3 diagnostic family, unversioned rewrite

**Multi-Agent Triage**:
A triage approach that splits responsibility across multiple collaborating agents, such as planner, investigator, critic, and reporter roles.
_Avoid_: V1 runtime, required architecture

**Expected Answer**:
The human-reviewed Diagnosis Ground Truth for an offline case, containing the expected diagnostic judgment and diagnosis-scoring fields but not the Required Evidence selection.
_Avoid_: Evidence Ground Truth, model answer, generated label, unverified ground truth

**Evidence Ground Truth**:
The trusted-evaluator artifact that records the hidden Required and Optional Evidence IDs used for evidence scoring and Oracle derivation, separately from the Expected Answer.
_Avoid_: Agent-visible corpus, Diagnosis Ground Truth, stored Oracle pack

**Expected Diagnosis**:
The diagnostic conclusion represented by an Expected Answer, including the preferred Failure Type and the essential causal and next-action claims that the Case evidence must support.
_Avoid_: Full Expected Answer artifact, evaluator prompt, model output

**Hybrid Curated Dataset**:
A human-reviewed evaluation set built from a mix of public failure samples and deliberately constructed cases to cover the project's failure types.
_Avoid_: Raw benchmark dump, synthetic-only dataset, unlabelled CI logs

**Failure Type**:
A stable category used to classify a CI or test failure so that reports, traces, and evaluations can be compared across runs.
_Avoid_: Error message, exception class, log snippet

**Triage Evaluation Metric**:
A criterion for judging whether a failure triage run produced a useful, evidence-backed report.
_Avoid_: System monitoring metric, business KPI

**Evaluation Suite**:
A named set of offline cases used to compare triage behavior across runtimes, prompts, tools, and retrieval strategies.
_Avoid_: Single demo case, ad hoc test

**Evaluation Suite Version**:
An immutable version of an evaluation suite with a fixed case set, expected answers, and case weighting.
_Avoid_: Mutable case folder, latest dataset

**Suite Fingerprint**:
A stable content identity for an evaluation suite version, used to detect whether its case set, case weights, or case artifacts changed.
_Avoid_: Suite name, directory timestamp

**Evaluation Report**:
A structured summary of evaluation results, including metric scores, baseline comparisons, and badcase observations.
_Avoid_: Raw logs, manual notes

**Evaluation Leaderboard**:
A comparison view of formal evaluation results for approved evaluation conditions under the same evaluation method.
_Avoid_: Debug run list, raw run history

**Formal Evaluation Run**:
An evaluation run executed from the approved evaluation matrix and used for leaderboard, regression, or badcase conclusions.
_Avoid_: Debug run, exploratory run

**Canonical Run**:
The formal evaluation run selected as the primary comparable result for an evaluation condition in ordinary leaderboard and badcase views.
_Avoid_: Stability sample, averaged repeated run

**Stability Sample**:
An additional repeated formal evaluation run for the same evaluation condition, used to measure variance and badcase consistency.
_Avoid_: Canonical run, debug run

**Debug Run**:
A local exploratory run used to inspect behavior while developing prompts, tools, retrieval, policies, or runtime code.
_Avoid_: Formal evaluation run, leaderboard result

**Case Subset Debug**:
A debug run over a selected subset of an evaluation suite, used for fast iteration on targeted cases or badcases.
_Avoid_: Formal evaluation run, suite result

**Badcase**:
A formal evaluation case where an evaluation condition fails a quality metric or quality gate, making it eligible for regression tracking and improvement analysis.
_Avoid_: Debug finding, anecdotal failure

**Badcase Carryover**:
A comparison of badcase outcomes between two formal evaluation conditions, identifying resolved badcases, persistent badcases, and new regressions.
_Avoid_: Editing old badcases, deleting history

**Badcase Reason**:
A structured reason assigned to a badcase to explain which part of triage quality failed and guide improvement work.
_Avoid_: Free-form complaint, raw error message

**Suggested Badcase Reason**:
A badcase reason proposed automatically by the evaluation scorer before human review.
_Avoid_: Reviewed badcase reason, final label

**Reviewed Badcase Reason**:
A badcase reason confirmed or corrected by a human reviewer for use in trusted analysis.
_Avoid_: Suggested badcase reason, raw scorer output

**Badcase Review**:
A human review activity for inspecting a formal badcase, correcting reviewed reasons, and recording reviewer notes.
_Avoid_: Issue workflow, multi-person approval

**Reviewer Note**:
A human-written note attached during badcase review to explain context, correction, or follow-up judgment.
_Avoid_: Chat comment thread, raw scorer explanation

**Debug Finding**:
An issue observed during local experimentation or case subset debug that has not yet been validated through formal evaluation.
_Avoid_: Badcase, leaderboard regression

**Evaluation Condition**:
The complete, named set of runtime, model, prompt, tool, retrieval, skill, policy, and budget settings used for one reproducible evaluation run.
_Avoid_: Runtime name only, project version only

**Evidence Acquisition Condition**:
The versioned experimental contract that defines how a runtime may observe and investigate a Case's Evidence Universe, such as deterministic Pipeline access, Full-context One-shot delivery, Fixed Model Workflow inputs, Static Retrieval, adaptive ReAct investigation, or Oracle Evidence delivery.
_Avoid_: Case contents, Runtime Variant alone, requirement that every condition has identical tools

**Oracle Evidence Diagnostic Condition**:
A controlled diagnostic evaluation condition that bypasses ordinary evidence discovery and supplies only the Human-reviewed Minimal Sufficient Evidence Set to a fixed model while withholding Evidence Ground Truth labels, Expected Answer, answer text, tool paths, scorer labels, and curator reasoning. Its runtime input is derived from Required Evidence IDs through Canonical Evidence Units back to Physical Artifacts; no independent Oracle Evidence artifact is frozen. It estimates conditional diagnosis performance when evidence acquisition difficulty is removed.
_Avoid_: Third V1 runtime, answer-key prompting, model capability proof, product candidate

**Effective Evaluation Condition**:
The fully resolved evaluation condition used for a run after applying any matrix defaults or one-level extension.
_Avoid_: Condition reference, unresolved matrix entry

**Condition Fingerprint**:
A stable content identity for an effective evaluation condition, used to detect whether the comparable experiment setup changed.
_Avoid_: Component fingerprint, condition name

**Model Configuration**:
The model provider, model name, provider-supported version or snapshot, and inference parameters used by a triage run.
_Avoid_: Component version, prompt version

**Evaluation Method**:
The versioned scoring contract used to judge triage runs, including metric definitions, scorer behavior, judge configuration, and report semantics.
_Avoid_: Evaluation backend, raw eval script, dashboard tool

**Evaluation Matrix**:
A controlled set of evaluation conditions selected for anchor comparison, ablation analysis, and candidate product comparison.
_Avoid_: Full Cartesian test grid, ad hoc run list

**Evaluation Matrix Version**:
A named version of the evaluation matrix that identifies a specific formal experiment design.
_Avoid_: Evaluation suite version, evaluation method version

**Anchor Condition**:
An evaluation condition rerun across evaluation method or runtime changes to keep leaderboard shifts interpretable.
_Avoid_: Random baseline run, smoke test

**Ablation Condition**:
An evaluation condition that changes one capability while holding the rest of the condition stable, so the effect of that capability can be isolated.
_Avoid_: Product variant, full system comparison

**Candidate Condition**:
A product-relevant complete evaluation condition used to compare deployable or demo-worthy system configurations.
_Avoid_: Ablation test, experimental toggle dump

**Failure Type Accuracy**:
The evaluation metric for whether a triage run selected the expected failure type.
_Avoid_: Root cause correctness

**Failure Type Exact Accuracy**:
The evaluation metric for whether a triage run selected the primary expected failure type exactly.
_Avoid_: Acceptable alternative rate, partial credit

**Failure Type Acceptable Rate**:
The evaluation signal for how often a triage run selected a reviewer-approved acceptable failure type instead of the primary expected failure type.
_Avoid_: Exact accuracy, full correctness

**Acceptable Failure Type**:
A reviewer-approved alternative failure type for a case that may receive partial credit or a warning status when the primary expected failure type is not selected.
_Avoid_: Loose label, unreviewed synonym

**Evidence Hit Rate**:
The evaluation metric for whether a triage report cites expected key evidence through valid evidence references.
_Avoid_: Retrieval recall, log coverage, evidence retrieved but not cited

**Retrieval Evidence Hit**:
An evaluation signal indicating that the runtime retrieved or inspected expected key evidence during the run trace.
_Avoid_: Report evidence citation, final answer correctness

**Report Evidence Hit**:
An evaluation signal indicating that the final structured triage report cited expected key evidence through valid evidence references.
_Avoid_: Retrieval-only hit, vague evidence mention

**Required Evidence**:
Human-reviewed Canonical Evidence Units referenced by hidden `required_evidence_ids` in Evidence Ground Truth that must be cited for a Case to satisfy the evidence quality requirement and together form its Minimal Sufficient Evidence Set. Existing scoring documentation may call this Required Key Evidence. It contains necessary facts without evaluator-authored answer text or reasoning.
_Avoid_: Optional evidence, supporting detail, answer annotation

**Minimal Sufficient Evidence Set**:
The inclusion-minimal, Human-reviewed set of source-faithful Required Key Evidence that contains the facts needed to derive the Expected Diagnosis under the fixed diagnosis contract; removing any item makes at least one necessary fact or disambiguation unavailable.
_Avoid_: Shortest possible context, complete Expected Answer, model-pass-tuned evidence bundle

**Optional Evidence**:
Expected evidence that can strengthen a triage report but is not required for the case to pass the evidence quality requirement.
_Avoid_: Required key evidence, irrelevant evidence

**Required Fields Completeness**:
The evaluation metric for whether a triage report includes the required diagnostic fields.
_Avoid_: Report length, writing quality

**Tool Path Validity**:
The evaluation metric for whether the triage run used a reasonable sequence of tools for the case.
_Avoid_: Tool count, latency

**Per-Failure-Type Score**:
An evaluation breakdown that reports metric performance separately for each failure type in the evaluation suite.
_Avoid_: Overall score only, raw case list

**Metric Vector**:
A set of evaluation metric values reported together without collapsing them into a single weighted score.
_Avoid_: Composite score, single leaderboard score

**Agent-System Realization Gap**:
A paired metric-vector difference between an Oracle Evidence Condition and a normal Agent Condition for the same Case under matching controlled settings. It estimates how much Oracle-condition diagnosis performance the Agent system did not realize and is reported by Case, metric, and Failure Type.
_Avoid_: One composite model score, causal proof, ordinary leaderboard rank

**Metric-Specific Ranking**:
A leaderboard ranking ordered by one evaluation metric at a time instead of a composite score.
_Avoid_: Overall winner, global rank

**Stability Metric**:
A repeated-run evaluation metric that describes score variance or badcase consistency for the same evaluation condition.
_Avoid_: Quality metric, single-run score

**Quality Metric**:
An evaluation metric that judges whether the triage result is correct, evidence-backed, complete, and follows a reasonable tool path.
_Avoid_: Cost metric, performance metric

**Quality Gate**:
A formal evaluation qualification status based on minimum quality metric thresholds for deciding whether an evaluation condition is eligible for candidate discussion.
_Avoid_: Eval job success, cost target

**Operational Metric**:
A metric that describes runtime cost, latency, token usage, step count, or tool call volume for a triage run.
_Avoid_: Quality metric, correctness score

**Test Assertion Failure**:
A failure caused by test expectations not matching observed behavior.
_Avoid_: Broken CI, flaky test

**Lint or Type Failure**:
A failure caused by static checks rejecting formatting, lint rules, or type correctness.
_Avoid_: Build failure, code quality issue

**Dependency or Install Failure**:
A failure caused by missing, incompatible, unavailable, or incorrectly installed project dependencies.
_Avoid_: Environment failure, package error

**Config or Environment Failure**:
A failure caused by missing, invalid, or inconsistent configuration, secrets, environment variables, or runtime settings.
_Avoid_: Dependency failure, infrastructure outage

**Timeout or Flaky Failure**:
A failure characterized by nondeterminism, excessive duration, or intermittent behavior without a stable product-code root cause.
_Avoid_: Test assertion failure, infrastructure outage

**Dev Agent**:
An agent specialized for software development work such as understanding repositories, diagnosing CI failures, following engineering SOPs, and producing development reports.
_Avoid_: General assistant, customer-service agent

**AgentOps**:
The operational discipline around agent runs, including traceability, evaluation, failure analysis, safety boundaries, and iterative improvement.
_Avoid_: Logging only, monitoring only

**Modern Agent Stack**:
The project learning scope covering agent runtime, tool use, retrieval, memory, planning, skill-style capability packaging, tracing, evaluation, and safety.
_Avoid_: External agent integration only

**Skill Package**:
A reusable packaged agent capability that may bundle prompts, tools, retrieval configuration, project knowledge, and operating instructions.
_Avoid_: Single tool, tool registry entry

**Reference Agent**:
A mature external coding agent studied as a reference architecture or used in an explicit comparison, not as the core implementation or semantics source of DevAgentOps. Pi's current canonical upstream is `earendil-works/pi`; `badlogic/pi-mono` is historical lineage only.
_Avoid_: Project foundation, implementation dependency, compatibility target, replacement implementation
