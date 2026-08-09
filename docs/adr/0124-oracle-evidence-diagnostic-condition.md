# Oracle Evidence Diagnostic Condition

## Status

Accepted.

## Context

DevAgentOps compares Fixed Pipeline, ReAct, retrieval, prompt, tool-policy, and model ablation conditions, but an Agent failure can still combine two different bottlenecks: acquiring the decisive evidence and reasoning correctly from evidence that is already available. Retrieval Evidence Hit and Report Evidence Hit localize part of this difference, but they do not answer whether the fixed model could diagnose the Case when evidence discovery difficulty is removed.

## Decision

V1 Evaluation Methodology will define an Oracle Evidence Diagnostic Condition, shortened to Oracle Evidence Condition. It is a controlled diagnostic evaluation condition, not a third V1 runtime or a product candidate.

For each eligible Case, the condition bypasses ordinary Agent evidence discovery and directly supplies the source-faithful evidence items referenced by the Human-reviewed `required_evidence_ids`. The supplied items form a Human-reviewed Minimal Sufficient Evidence Set: under the fixed model, diagnosis prompt, report contract, scorer, and inference settings, they contain the facts necessary to derive the Expected Diagnosis, and no proper reviewed subset is sufficient. Minimality and sufficiency are review judgments, not properties inferred from an Oracle model pass.

The Oracle input may include stable Evidence IDs and their frozen source content so the model can produce normal Evidence References. It must not include or derive from model-visible evaluator annotations such as:

- Expected Answer labels or answer text;
- Primary or acceptable Failure Type labels;
- curator reasoning, evidence-selection rationale, or scorer labels;
- fix commit, passing revision, or reasonable tool path;
- evaluator-authored root-cause or recommended-action summaries.

Evidence ordering and delivery wrappers must be deterministic, versioned, fingerprinted, and free of evaluator commentary. The Expected Answer and the fact that an item is tagged required remain inside the Trusted Evaluator boundary; only the selected source evidence content is delivered.

Oracle and a paired Agent condition must keep the Evaluation Suite and Case versions, model configuration, diagnosis prompt and Structured Triage Report contract, evaluation method and diagnosis scorer, inference parameters, output budget, and context/truncation policy equal wherever applicable. Evidence delivery and the discovery/tool path are the intended intervention. Any unavoidable wrapper or runtime difference must be recorded in the Effective Condition and Run Manifest; a comparison with other behavior-affecting differences is not a valid realization-gap pair.

Agent-System Realization Gap is reported as a paired, higher-is-better metric-vector difference, never as an implicit composite score:

```text
realization_gap(case, metric) = oracle_score(case, metric) - agent_score(case, metric)
```

Each metric is reported by Case, overall, and per Failure Type. Diagnosis/report metrics may participate in the gap. Retrieval, tool-path, step-count, tool-call, cost, and latency measurements remain separate acquisition or operational diagnostics because Oracle intentionally removes ordinary discovery. PASS/FAIL quadrant analysis may be derived only from a versioned diagnosis-quality predicate; it does not replace the metric vector.

Oracle performance is an upper-bound diagnostic estimate under reviewed evidence packaging, not proof of a model's context-independent reasoning ability. Oracle failure can support a model-bottleneck hypothesis only after auditing evidence sufficiency, answer leakage, prompt/report constraints, scorer consistency, truncation, and run variance.

## Alternatives Considered

- Infer model capability from ReAct versus Pipeline alone. Both conditions still include evidence acquisition and can fail before the model sees the decisive facts.
- Expose the complete Expected Answer. This turns diagnosis into answer reproduction and violates the Trusted Evaluator boundary.
- Treat Oracle as a new runtime variant. It is an experimental intervention on evidence delivery, not a deployable triage workflow.
- Collapse the difference into one score. V1 has no defensible composite weighting and requires metric-specific, per-Failure-Type analysis.

## Consequences

DevAgentOps can distinguish likely Agent-system opportunities from likely model, prompt/report, scorer, or dataset bottlenecks more precisely. The condition also increases curation burden: every Oracle-eligible Case needs Human review for sufficiency, minimality, provenance fidelity, and answer non-encoding. Changing that reviewed evidence set changes the Case and Suite identity.

Oracle-versus-Agent results are paired diagnostic analyses, not ordinary direct leaderboard rankings. Unexpected `Oracle FAIL + Agent PASS` outcomes become evaluation-audit signals rather than evidence that the Agent exceeded an Oracle ceiling.

## Implementation Notes

- Add a future explicit, fingerprinted evidence-delivery field or equivalent versioned contract to Evaluation Matrix Conditions and Run Manifests; do not overload `runtime_variant`.
- Build the Oracle pack by resolving reviewed Required Evidence IDs to frozen log chunks or repository evidence items, then strip all Expected Answer fields and curator metadata.
- Reject Oracle eligibility when evidence is missing, mutable, unsanitized, non-source-faithful, or not Human reviewed as minimal and sufficient.
- Validate pairing keys before computing a gap and record every differing field.
- Keep canonical runs and stability samples separate. Use repeated runs to audit variance rather than silently averaging them.
- Implement execution and gap reporting in [Issue #19](https://github.com/ultrabababa/dev-agentops-platform/issues/19). Do not expand Issue #15, which remains responsible for curating the balanced Formal Evaluation Suite, or Issue #16, which remains the deterministic Pipeline Baseline tracer bullet.

## Implementation Guide

See [Oracle Evidence Diagnostic Condition and Agent-System Realization Gap](../evaluation/oracle-evidence-diagnostic-condition.md).

## Refines

ADRs: `0113`, `0115`, `0116`, `0118`, `0122`, `0123`.
