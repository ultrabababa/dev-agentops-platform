# L3 Static Retrieval V1 — Implementation Design

Status: Design frozen and V1 implemented on 2026-08-23. Deterministic tests, Component/Matrix validation, full-suite doctor, tiny fake-provider qualification, a live smoke run, and a clean MiniMax-M3 20-Case × 3 repeats formal milestone are complete. The completed baseline and evaluator-side acquisition analysis are recorded in [L3 Static Retrieval V1 Formal Milestone](milestones/l3-static-retrieval-2026-08-24.md).

Normative architecture decision: [ADR 0130](../adr/0130-l3-static-retrieval-v1-contract.md).

This document is the implementation guide for the first `static_retrieval` diagnostic condition. It intentionally stops at a strong, deterministic lexical baseline; qualification evidence, not pre-emptive feature growth, should drive later retrieval changes.

## 1. Goal and experiment boundary

L3 V1 answers one narrow question:

> What changes when the one-shot triage model receives a deterministic retrieved subset of the same frozen Physical Evidence Universe instead of L1's complete upfront universe?

The target comparison is therefore:

```text
L1
Physical Artifacts -> complete serialization -> Model x1 -> Report

L3
Physical Artifacts -> deterministic static retrieval -> selected serialization -> Model x1 -> Report
```

Do not turn L3 into a second Agent runtime. There is no model decision inside retrieval and no adaptive search loop.

## 2. Frozen V1 configuration

The first frozen `retriever_config` must encode behavior equivalent to:

```yaml
strategy: static_bm25_multi_query_rrf_v1
settings:
  corpus_scope: case_physical_artifacts

  chunking:
    strategy: fixed_line_window_v1
    window_lines: 100
    overlap_lines: 20

  signal_extraction:
    log_extractor_version: failure_signal_extractor_v1
    repo_extractor_version: repo_signal_extractor_v1
    per_signal_type_cap: 5
    deduplicate: normalized_content_keep_latest
    priority: specificity_then_later_line

  tokenizer:
    version: code_aware_lexical_v1
    lowercase: true
    preserve_compound_token: true
    split_path_separator: true
    split_dot: true
    split_underscore: true
    split_hyphen: true
    split_camel_case: true
    stemming: false
    stopword_removal: false

  ranker:
    implementation: bm25s
    implementation_version: 0.3.10
    method: lucene
    k1: 1.5
    b: 0.75
    per_query_candidates: 20

  fusion:
    strategy: reciprocal_rank_fusion
    rank_constant: 60
    query_weights: uniform

  selection:
    log_top_k: 10
    repository_top_k: 10
    redistribute_unused_slots: false

  packing:
    exact_chunk_deduplication: true
    overlapping_span_coalescing: true
    same_physical_source_only: true
    bridge_unretrieved_gaps: false
    backfill_after_merge: false
```

The exact manifest shape must conform to the existing Component Registry schema: `component_type=retriever_config`, with `behavior.strategy` and `behavior.settings`. Freeze the final manifest through the existing component workflow rather than hand-editing fingerprints.

There is deliberately no standalone `retrieval_corpus_version` for `triage-suite-v1`; Case/Suite fingerprints already identify the frozen corpus content.

## 3. End-to-end flow

```text
RuntimeCaseWorkspace
│
├─ raw.log
│    ├─ build 100/20 chunks
│    ├─ scan complete raw.log with deterministic failure-signal extractor
│    ├─ normalize / dedup / priority / max 5 per signal type
│    ├─ one lexical query per selected signal
│    ├─ BM25 Top-20 per query
│    ├─ equal-weight RRF(k=60)
│    └─ final Top-10 log chunks
│
└─ frozen repository snapshot
     ├─ build 100/20 chunks per file
     ├─ index repository-relative path tokens + chunk-content tokens
     ├─ extract repo-oriented queries from selected log evidence
     ├─ one lexical query per selected signal
     ├─ BM25 Top-20 per query
     ├─ equal-weight RRF(k=60)
     └─ final Top-10 repo chunks

selected chunks
    -> physical overlap coalescing
    -> map packed spans to overlapping Canonical Evidence coordinates
    -> static_retrieval_runtime_input_v1
    -> shared L1 Task Contract + output suffix
    -> exact token preflight
    -> one LogicalCompletionRequest
    -> shared Evidence Reference Canonicalization
    -> report validation / frozen scorer
```

## 4. Suggested code boundaries

Keep retrieval mechanics independent from the L3 condition wrapper. A practical layout is:

```text
src/devagentops/retrieval/
    __init__.py
    types.py
    chunking.py
    tokenization.py
    signals.py
    bm25_v1.py
    fusion.py
    packing.py
    static_v1.py

src/devagentops/conditions/l3/
    __init__.py
    static_retrieval_v1.py
    executor.py
```

Names may be adjusted to existing repository conventions, but keep these semantic boundaries:

- retrieval package: deterministic evidence-acquisition implementation;
- `conditions/l3`: Treatment validation, model-visible serialization, provider call, and condition execution;
- evaluation layer: Matrix dispatch, formal identity, Trace/persistence/scoring integration.

Do not put hidden evaluator-ground-truth logic inside `src/devagentops/retrieval/` or `conditions/l3/`.

## 5. Core data contracts

Use typed immutable values where practical. Exact class names are not normative, but the implementation needs equivalent information.

```text
RetrievalChunk
- chunk_id
- source_kind: raw_log | repository_file
- source_path
- repository_relative_path? 
- start_line
- end_line
- content
- content_sha256

RetrievalQuery
- query_id
- pool: log | repository
- signal_type
- normalized_text
- source_line? / provenance span?

PerQueryHit
- chunk_id
- query_id
- bm25_score
- bm25_rank

FusedHit
- chunk
- rrf_score
- fused_rank
- contributing per-query hits

PackedSpan
- source_kind
- source_path
- start_line
- end_line
- content
- derived_from_chunk_ids
- overlapping_canonical_evidence_ids
```

Chunk IDs and ordering must be deterministic from source identity + physical span; they must not depend on Python object identity, iteration accidents, or random UUIDs.

## 6. Chunking semantics

For each physical file independently:

```text
1-100
81-180
161-260
...
```

Use physical 1-based line coordinates compatible with `RuntimeCaseWorkspace` / Canonical Evidence source coordinates. Never concatenate repository files before chunking.

Do not use Canonical Evidence Units as the chunk source. The two flows remain:

```text
Physical Artifact -> Retrieval Chunker -> runtime-specific chunks
Physical Artifact -> Canonicalization Profile -> stable evaluation coordinates
```

## 7. Tokenizer semantics

Tokenizer V1 is a deterministic DevAgentOps function. `bm25s` receives already-tokenized documents/queries.

For a technical token, retain both its normalized compound representation and useful subtokens. Examples:

```text
FooService.java
-> fooservice.java, fooservice, foo, service, java

retry_on_error
-> retry_on_error, retry, on, error

retryOnError
-> retryonerror, retry, on, error

com.foo.Bar
-> com.foo.bar, com, foo, bar
```

Do not add stemming or generic NLP stopword deletion. Avoid path n-gram/hierarchy expansion in V1.

Repository indexing tokenizes both:

```text
repository-relative path metadata
+
chunk content
```

Path metadata is included once as ordinary lexical evidence; do not introduce field/path boosting in V1.

## 8. Signal extraction semantics

The extractors are intentionally conservative deterministic heuristics, not language-complete parsers.

### 8.1 Log failure signals

Scan the complete raw log and emit candidates from recognizable forms such as:

- test failure names/identifiers;
- exceptions/errors with optional messages;
- assertions and compiler/linter/type-check diagnostics;
- specific error/failure message lines;
- stack frames, file:line references, paths, classes, methods, functions, symbols.

Normalize obvious formatting noise/whitespace for equality and query text. Deduplicate equal normalized signals and keep the latest physical occurrence.

When a signal family has more than five candidates, deterministic selection is:

```text
specific diagnostic/entity before generic boilerplate
then later physical line before earlier line
```

Do not assign different query weights by signal type.

### 8.2 Repository query signals

Extract from the selected log chunks/spans after log retrieval. Preserve both code-oriented and semantic signals:

```text
path / filename
class / method / function / symbol
test identifier
exception / error type
meaningful diagnostic / error message
```

Again cap each signal family at five after normalization/dedup/priority.

V1 does not add an adaptive/model-generated fallback. If a pool yields no valid queries, the zero-query/zero-selection state must be explicit in Trace rather than silently changing retrieval policy. Qualification can justify a later frozen fallback if this actually occurs.

## 9. BM25 and RRF

Add `bm25s==0.3.10` as the V1 retrieval dependency and instantiate it with explicit parameters:

```text
method = lucene
k1 = 1.5
b = 0.75
```

Do not rely on implicit library defaults in formal identity.

Each query retrieves at most 20 candidates from its pool. If a pool has fewer chunks, use the available set.

Fuse candidate ranks using 1-based equal-weight RRF:

```text
rrf_score(chunk) = sum(1 / (60 + rank_q(chunk)))
```

A chunk absent from a query's candidate list contributes zero for that query.

Use an explicit deterministic tie-break after RRF score, for example:

```text
rrf_score descending
best contributing BM25 rank ascending
source_path ascending
start_line ascending
```

The tie-break is for reproducibility, not an additional relevance model.

## 10. Pool selection and packing

Keep log and repository pools separate through final selection:

```text
max 10 log chunks
max 10 repo chunks
```

Do not redistribute unused slots.

After Top-K is frozen, pack selected evidence without changing retrieval selection:

```text
same file 1-100 + 81-180  -> 1-180
same file 1-100 + 161-260 -> two spans
A.java + B.java            -> never merge
```

Coalescing removes repeated model-visible bytes only. It must not expose any unretrieved line between disjoint spans. It must not trigger selection of rank 11+ chunks to refill a quota.

Keep original selected chunks and ranking provenance in Trace even when multiple chunks become one packed span.

## 11. Serialization and model call

Create a distinct serialization identity:

```text
static_retrieval_runtime_input_v1
```

The serialized document should follow the L1 one-shot shape where useful but must make selected evidence explicit. It should contain conceptually:

```json
{
  "runtime_input_serialization_version": "static_retrieval_runtime_input_v1",
  "case": {},
  "evidence_delivery": {
    "mode": "deterministic_static_retrieval"
  },
  "retrieved_physical_evidence": [
    {
      "kind": "raw_log | repository_file",
      "path": "...",
      "start_line": 1,
      "end_line": 100,
      "content": "...",
      "overlapping_canonical_evidence_ids": ["..."]
    }
  ]
}
```

Do not expose BM25 score, RRF score, retrieval rank, hidden Required Evidence, Expected Answer, or evaluator labels in this serialization.

For ordering:

- log packed spans: physical line ascending;
- repository files: best selected retrieval rank first;
- spans within one repository file: physical line ascending.

Use `structured-triage-task-contract-v1` and the existing output-contract suffix. Issue exactly one configured `LogicalCompletionRequest` after retrieval.

Reuse the configured L1 exact-token preflight semantics:

```text
input_tokens + max_completion_tokens <= context_limit_tokens
```

Do not silently truncate retrieved evidence. If the frozen selection cannot fit, fail as context-infeasible; a future budget-aware selector would be a different Treatment.

## 12. Canonical evidence mapping and final report

For every selected/packed physical span, deterministically map by source identity + physical line overlap to answer-neutral Canonical Evidence coordinates already available through the Case workspace/package.

This mapping exists for citation identity, measurement, and Trace. It must never consult:

```text
required-evidence.json
expected-answer.json
previous eval results
badcase reports
```

After the model returns its candidate report, L3 must enter the same shared Evidence Reference Canonicalization + validation + frozen scoring path used by current model-backed conditions. Do not create an L3-only fuzzy citation resolver.

## 13. Trace requirements

Trace/debug data should make retrieval reproducible without leaking ranking hints into the prompt. At minimum preserve:

- retriever component version/fingerprint;
- selected normalized signals/queries and their pool/type;
- final selected chunk identities and physical spans;
- for selected chunks, contributing BM25 rank/score and RRF score/rank;
- packed spans and `derived_from_chunk_ids`;
- overlapping Canonical Evidence IDs;
- runtime-input hash/byte count and exact-token preflight observation;
- the single model-call lifecycle using existing provider execution conventions.

It is not necessary for V1 to persist every Top-20 candidate for every query as a first-class formal artifact. Add richer candidate dumps only if qualification debugging demonstrates a need.

A future evaluator-side `retrieval_evidence_exposure` diagnostic may compare exposed Canonical IDs with hidden Required Evidence. Do not make that diagnostic a runtime dependency or new formal quality score in the initial implementation.

## 14. Matrix and Component Registry integration

The L3 formal Matrix condition remains schema v2 and uses:

```text
runtime_variant = static_retrieval
```

Treatment contracts should reference at least:

- shared Task Contract `prompt`;
- frozen L3 `retriever_config` component;
- L3 runtime-input serialization version;
- existing output contract;
- provider/model/reasoning/generation/context settings matching the intended L1 comparison.

Extend Matrix/doctor validation so `static_retrieval` requires a valid frozen retriever component version/fingerprint. Do not change historical condition fingerprints or retroactively insert retriever contracts into L1/L2/Oracle/L4.

Use the existing Component Registry freeze path to create the immutable L3 retriever version and update `components/registry.json`.

## 15. Integration points to inspect

Implementation should inspect and reuse current code rather than fork contracts unnecessarily. Expected touch points include:

```text
pyproject.toml
components/frozen/retriever_config/            # new frozen component location
components/registry.json
src/devagentops/retrieval/                     # new deterministic retrieval package
src/devagentops/conditions/l3/                 # new condition wrapper/executor
src/devagentops/evaluation/matrix_v2.py        # L3 retriever contract validation
src/devagentops/evaluation/run_v2.py           # static_retrieval dispatch
src/devagentops/evaluation/development_treatment.py
src/devagentops/evaluation/trace.py             # only if new typed payload support is needed
evaluation/matrices/...                         # follow existing matrix naming/layout
```

Also inspect and reuse:

```text
conditions/l1/full_context_v1.py                # one-shot + exact-preflight pattern
conditions/l1/executor.py                       # executor/scoring integration
runtime/workspace.py                            # frozen physical access + canonical coordinates
conditions/oracle/*                             # selected-evidence serialization ideas only; never Oracle selection semantics
shared Evidence Reference Canonicalization path # final report realization
```

Do not copy Oracle's hidden Required Evidence selection logic into L3.

## 16. Deterministic acceptance tests

Add focused unit/integration tests before any live model qualification.

Required gates:

1. **Chunking** — 100/20 windows, short final chunk, no cross-file chunk.
2. **Tokenizer** — compound + delimiter + camelCase tokens, lowercase, no stemming/stopword behavior.
3. **Signals** — deterministic extraction, normalized dedup keeps latest, specificity priority, max five/family.
4. **BM25/RRF** — Top-20/query, k=60 equal-weight fusion, deterministic ties.
5. **Pool isolation** — log and repo quotas remain 10/10 maximum; no cross-pool backfill.
6. **Repo path indexing** — path/filename query can retrieve a file chunk through path metadata.
7. **Packing** — true overlaps coalesce; gaps/files never bridge; no post-merge backfill.
8. **Serialization** — only selected Physical Artifact content + answer-neutral canonical mappings are model-visible; no ranking/evaluator metadata.
9. **Model path** — exactly one provider logical request after retrieval and L1-style exact-token preflight.
10. **Leakage** — L3 runtime/retrieval code has no dependency on Required Evidence or Expected Answer.
11. **Regression** — existing L1/L2/Oracle/L4 deterministic tests remain green.

## 17. Implementation order

Keep the first implementation short and observable:

```text
1. add/pin bm25s
2. retrieval types + chunker + tokenizer
3. signal extraction
4. BM25 + RRF + source quotas
5. overlap packing + canonical mapping
6. freeze retriever_config component
7. L3 one-shot serialization/executor
8. Matrix/doctor/run_v2 integration
9. deterministic tests
10. run a very small qualification subset and inspect Trace
11. only then prepare a formal L3 matrix/run
```

Do not tune against `triage-suite-v1` hidden Required Evidence / Expected Answer during implementation. If retrieval optimization becomes necessary later, create a separate calibration/dev set, freeze the chosen configuration, and only then run the formal suite.

## 18. Out of scope for this implementation

Do not add, unless a separate decision is made after qualification evidence:

```text
embedding/vector retrieval
vector database
Elasticsearch/OpenSearch service
neural reranker
MMR
query LLM
AST chunker
language-specific parser
dynamic chunk size
dynamic Top-K
source quota tuning
repair/sandbox/test execution
```

The first milestone is a correct, reproducible L3 evidence-acquisition baseline, not an optimized RAG stack.
