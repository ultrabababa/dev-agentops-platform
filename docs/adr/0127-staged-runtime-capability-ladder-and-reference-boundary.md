# Staged Runtime Capability Ladder and Reference Boundary

## Status

Accepted.

## Context

The earlier V1 plan compared a deterministic Pipeline directly with a self-built ReAct runtime. That comparison remains useful, but it cannot by itself attribute an uplift to model reasoning, fixed model-backed orchestration, evidence acquisition, or adaptive Agent control. DevAgentOps needs intermediate diagnostic conditions that introduce these capabilities separately without expanding the Product Runtime surface.

The project also benefits from studying a mature Agent runtime architecture while preserving its own bounded Investigation Workspace, evaluation-first design, explicit tool policy, and trusted-evaluator boundary.

## Decision

DevAgentOps adopts the following **Runtime Capability Ladder** as an evaluation and attribution model:

| Level | Capability name | Role | Added capability |
| --- | --- | --- | --- |
| L0 | `deterministic_pipeline` | Product Runtime baseline | deterministic execution with no model and no Agent |
| L1 | `full_context_one_shot` | diagnostic/comparison condition | fixed prompt and exactly one model call over the complete Agent-visible Evidence Universe |
| L2 | `fixed_model_workflow` | diagnostic/comparison condition | program-controlled, fixed multi-stage model orchestration |
| L3 | `static_retrieval` | evidence-acquisition diagnostic condition | static retrieval over the Evidence Universe, without adaptive Agent control |
| L4 | `self_built_react` | Product Runtime and first Agentic Runtime | adaptive decision, tool, observation, context, stop, and report loop |
| L5+ | incremental Agent capabilities | future Product Runtime evolution or controlled conditions | retrieval, context management, planning, verifier, skills, experience, and later capabilities |

The ladder is not a mandatory implementation order. In particular, this decision does not require L3 to be implemented before L4. It is a semantic structure for controlled comparisons: conditions should add or remove capabilities deliberately so observed changes are not automatically attributed to “the Agent.”

V1 Product Runtime remains limited to **Fixed Pipeline** and **self-built ReAct**. L1, L2, and L3 are model-backed diagnostic/comparison conditions, not additional Product Runtimes. L4 is the first condition with adaptive Agent control and begins the long-lived self-built Agent Runtime kernel lineage.

The shipped Issue #16 identity remains `runtime_variant="pipeline_baseline"`. `deterministic_pipeline` is the L0 capability-level name, not a request to rename historical manifests, runtime identities, Matrix values, or Registry entries. This ADR does not change Matrix or Registry schemas and does not freeze a future field name for recording ladder level or condition semantics.

### L1 full-context integrity

L1 means that the complete **Agent-visible Evidence Universe** for the condition is delivered to the model in one fixed prompt and one model call. It must not silently truncate the evidence and continue to claim `full_context_one_shot` semantics. If the complete visible universe exceeds the condition's fixed context budget, a truncated run is not a valid L1 full-context result.

The first L1 implementation records an execution/feasibility failure with zero provider calls when the complete rendered input plus the reserved output tokens exceeds the fixed model context capability. It does not truncate, summarize, split, retry, or relabel the condition.

### Task Contract and Runtime Control Separation

Controlled comparisons should reuse the same versioned Task Contract where scientifically appropriate. The Task Contract defines the diagnosis task, taxonomy, grounding and citation rules, and final Structured Triage Report contract. Evidence delivery, tools, Retrieval, stages, loops, call count, and stop rules belong to the Runtime condition rather than the shared Task Contract.

`runtime_input` is a case-specific data plane. It may carry Case identity, forbidden actions, evidence, answer-neutral citation coordinates, artifact boundaries, and descriptive serialization metadata, but it must not conceal imperative Runtime control policy. Any model-visible Runtime control instructions that vary across conditions must be explicit, versioned, and recorded as treatment. Sharing a Task Contract therefore does not imply byte-identical rendered requests.

### Oracle is orthogonal

Oracle Evidence remains an orthogonal diagnostic intervention under ADR 0124. It changes evidence delivery by resolving the hidden Human-reviewed Minimal Sufficient Evidence Set for a fixed model; it is not a capability rung and must not be presented as L1, L2, L3, or a Product Runtime.

### Pi reference-architecture boundary

[`earendil-works/pi`](https://github.com/earendil-works/pi) is the current canonical upstream for the project's primary Agent Runtime reference architecture. `badlogic/pi-mono` is recorded only as historical lineage and an old repository name; it is not the current canonical reference.

DevAgentOps may study Pi's mature treatment of Agent state, loop structure, tool interface, event flow, model-provider seam, stop conditions, and context management when designing the formal ReAct runtime. Pi is:

- a reference architecture only;
- not an implementation dependency;
- not a compatibility target;
- not the source of DevAgentOps Runtime semantics;
- not authorization to copy its concrete API into project contracts.

DevAgentOps will implement its own Runtime and retain the bounded Investigation Workspace, evaluation-first contracts, Trusted Evaluator and leakage boundaries, explicit tool policy, and V1 diagnosis-only product boundary. A concrete Pi API/reference matrix is deferred until formal ReAct design, when the project has a specific kernel contract to compare.

## Alternatives Considered

- Compare only deterministic Pipeline and complete ReAct. This keeps the Product Runtime list small but cannot isolate which added capability produced an uplift.
- Promote every ladder level to a Product Runtime. This would inflate V1 product scope and confuse diagnostic scaffolds with supported runtime products.
- Require strict L0-to-L4 implementation order. The evaluation semantics do not require delivery sequencing, and the value or cost of L3 may be learned independently.
- Make Oracle another ladder level. Oracle removes ordinary evidence-discovery difficulty rather than adding a runtime capability.
- Adopt Pi as a dependency or compatibility contract. This would surrender project-specific semantics and prematurely freeze an external API boundary.

## Consequences

Positive consequences:

- Evaluation can distinguish model reasoning, fixed orchestration, static evidence acquisition, and adaptive Agent control.
- V1 keeps only two Product Runtime identities while still supporting informative diagnostics.
- The self-built ReAct kernel can learn from mature architecture without inheriting external semantics or dependency risk.
- L1 results cannot hide context loss behind a misleading full-context label.

Tradeoffs:

- More diagnostic conditions may require additional controlled runs and explicit manifests in later implementation issues.
- Comparisons require care to hold the Case, base model, prompt/report contract, scorer, inference settings, and other relevant controls fixed.
- The concrete encoding of capability level, L1 over-budget handling, L2 stages, L3 retrieval parameters, and Pi reference matrix remain future design work.

## Non-Decisions

- No L2, L3, ReAct, retrieval, tool, or context-management implementation is selected here.
- The implementation order between L3 and L4 is not frozen.
- No Matrix, Registry, Run Manifest, or runtime schema field is added or named.
- No Pi API or DevAgentOps-to-Pi mapping is frozen.
- Investigation Workspace, Trusted Evaluator, leakage, Canonical Evidence, and tool-policy contracts are unchanged.

## Implementation Guide

See [Runtime Capability Ladder and Model-backed Diagnostic Conditions](../evaluation/runtime-capability-ladder.md).

## Refines

ADRs: `0002`, `0112`, `0113`, `0124`, `0125`.
