# DevAgentOps

DevAgentOps is a learning and job-seeking project for building a developer-focused agent platform end to end. Its primary domain is CI/Test Failure Triage AgentOps.

## Language

### **DevAgentOps**:

A developer-focused agent platform that combines CI/test failure triage with operational visibility, evaluation, and governance.
_Avoid_: Generic coding assistant, chatbot, Codex clone

### **CI/Test Failure Triage AgentOps**:

The project domain for making automated build and test failure diagnosis traceable, evaluable, repeatable, and governable.
_Avoid_: Generic CI/CD diagnosis, general coding agent, generic AgentOps platform

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

**Case Fingerprint**:
A stable content identity for an offline case package, used to detect whether its evidence, expected answer, or scoring-relevant manifest fields changed.
_Avoid_: Case name, suite fingerprint

**Log Evidence**:
The relevant CI or test output fragments used to support a triage judgment.
_Avoid_: Full raw log, prompt context

**Repository Evidence**:
The relevant source, configuration, dependency, or test files used to support a triage judgment.
_Avoid_: Full repository context, codebase dump

**Evidence Reference**:
A structured citation in a triage report that points to a specific log, repository, or project-knowledge evidence item.
_Avoid_: Vague evidence summary, unsupported claim

**Stable Evidence ID**:
A deterministic evidence identifier defined by a case package or retrieval corpus so expected answers, reports, and scorers can refer to the same evidence item.
_Avoid_: Runtime-only evidence label, generated display number

**Derived Evidence**:
An evidence item created during runtime by retrieval, extraction, or summarization that preserves provenance back to stable evidence or source spans.
_Avoid_: Stable evidence source, unsupported summary

**Project Knowledge**:
The SOPs, runbooks, documentation, and project notes used to interpret or respond to failure cases.
_Avoid_: Chat history, external issue tracker

**Agent Memory**:
Cross-run information made available to an agent from previous interactions, runs, or learned experience.
_Avoid_: Run trace, project knowledge, retrieved evidence

**Triage Knowledge Source**:
A local evidence source available to the triage agent, limited in V1 to log evidence, repository evidence, and project knowledge.
_Avoid_: Live issue tracker, team chat, external wiki

**Log Preprocessing**:
The preparation of raw CI or test output into concise summaries and retrievable evidence fragments before agent triage.
_Avoid_: Full-log prompting, manual log reading

**Retrieval Corpus**:
The versioned set of project knowledge and repository evidence indexed for retrieval during triage.
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
A fixed triage workflow used as the comparison point for agent runtime experiments.
_Avoid_: Agent runtime, production workflow

**Runtime Variant**:
An independently runnable triage runtime or workflow implementation that can be compared against other variants using the same evaluation suite.
_Avoid_: Project version, copied project directory

**Multi-Agent Triage**:
A triage approach that splits responsibility across multiple collaborating agents, such as planner, investigator, critic, and reporter roles.
_Avoid_: V1 runtime, required architecture

**Expected Answer**:
The human-reviewed reference judgment for an offline case, including the expected failure type, key evidence, required report fields, and reasonable tool path.
_Avoid_: Model answer, generated label, unverified ground truth

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

**Required Key Evidence**:
Expected evidence that must be cited for a case to satisfy the evidence quality requirement.
_Avoid_: Optional evidence, supporting detail

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
A mature external coding agent used as a comparison point or optional integration target, not as the core implementation of DevAgentOps.
_Avoid_: Project foundation, replacement implementation
