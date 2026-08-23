# ADR 0130 — L3 Static Retrieval V1 Contract

Status: Accepted — Human design freeze on 2026-08-23

## Context

ADR 0127 defines L3 `static_retrieval` as an optional evidence-acquisition diagnostic between L1 full-context one-shot and L4 adaptive investigation. L3 has not yet been implemented.

The purpose of L3 V1 is narrow: isolate the effect of **program-controlled static evidence acquisition** while keeping the downstream model path as close as practical to L1. L3 is not a general RAG product, not a vector-search platform, and not a new Product Runtime.

The formal `triage-suite-v1` Evidence Universe is already frozen per Case as Physical Artifacts (`raw.log` plus the exact-revision repository snapshot). Canonical Evidence provides stable answer-neutral citation/measurement coordinates but is not a required Retrieval chunking scheme. Required Evidence and Expected Answer remain evaluator-only labels.

The current Case scale is also deliberately bounded: logs range from very small files to roughly 2 MB, while repository snapshots contain a small, curated-but-natural set of frozen files. This favors a local deterministic baseline over external retrieval infrastructure.

## Decision

### 1. Runtime identity and comparison boundary

L3 V1 uses:

```text
runtime_variant = static_retrieval
```

Its model path is:

```text
Physical Evidence Universe
    -> deterministic static retrieval
    -> selected physical evidence
    -> one fixed Task Contract model call
    -> Structured Triage Report
```

L3 therefore compares most cleanly with L1:

```text
L1 = full evidence + one-shot model
L3 = retrieved evidence + one-shot model
```

The model does not generate retrieval queries, choose tools, decide the next search action, or decide when retrieval stops. The Retriever may programmatically scan the complete Agent-visible Physical Artifacts in order to build indexes and extract deterministic signals. The **model** sees only the selected evidence subset.

### 2. Corpus scope and identity

For `triage-suite-v1`, the retrieval corpus is fixed to:

```text
case_physical_artifacts
```

L3 V1 does **not** introduce a separate `retrieval_corpus_version`. The Case/Suite fingerprints already identify the frozen Physical Artifact content, and the L3 treatment only needs to version retrieval behavior.

If future conditions add shared project knowledge, runbooks, cross-Case corpora, or any independently mutable retrieval corpus, that corpus must receive its own explicit identity and leakage boundary.

### 3. Frozen Retriever component

Behavior-affecting retrieval configuration is represented by a frozen Component Registry entry of type:

```text
retriever_config
```

The V1 component strategy is conceptually:

```text
static_bm25_multi_query_rrf_v1
```

The component settings must freeze chunking, signal extraction policy/version, tokenization policy/version, BM25 implementation/parameters, per-query candidate depth, RRF parameters, source quotas, and context-packing behavior. Implementation provenance remains additionally attributable through `code_revision`.

### 4. Retrieval chunks

Both log and repository Physical Artifacts use the same generic line-window chunker:

```text
window_lines  = 100
overlap_lines = 20
stride_lines  = 80
```

Rules:

- chunks never cross Physical Artifact file boundaries;
- the final short window is kept;
- short files naturally produce one chunk;
- chunk size is not dynamically changed per Case;
- Canonical Evidence Units are not reused as Retrieval chunks.

### 5. Separate log and repository pools

Log and repository evidence are retrieved separately so a large log cannot consume every retrieval slot.

Frozen V1 selection budget:

```text
log final_top_k        = 10
repository final_top_k = 10
cross-pool backfill    = false
```

If a pool contains fewer than its quota, all available selected chunks are used and unused slots are not transferred to the other pool.

### 6. Deterministic multi-query acquisition

#### Log retrieval

The Retriever may scan the complete `raw.log` to extract deterministic failure-oriented signals. V1 signal families are:

- failed test identifiers;
- exception/error types and exception messages;
- assertion, compiler, linter, or type-check diagnostics;
- specific `ERROR` / `FAILURE` messages;
- file/line, path, class, method, function, or symbol references.

Signal handling is deterministic:

```text
extract
-> normalize
-> deduplicate
-> specificity priority
-> same-priority later-line-first tie break
-> cap at 5 signals per signal family
```

After normalization, duplicate signals keep the latest physical occurrence. Specific diagnostics/entities outrank generic boilerplate such as bare `build failed` / `test failed` lines. Priority affects signal selection only; query weights remain uniform.

Each selected signal becomes an independent lexical query. For each query:

```text
BM25 candidate_top_k = 20
```

Candidate ranked lists are fused with equal-weight Reciprocal Rank Fusion (RRF):

```text
rrf_k = 60
score(chunk) = sum_q 1 / (60 + rank_q(chunk))
```

Ranks are 1-based. The final log selection is the fused Top-10 unique chunks. V1 does not add model-generated query rewriting or adaptive retrieval fallback.

#### Repository retrieval

Repository queries are extracted deterministically from the **selected log evidence**, not from evaluator labels. Query signal families include:

- path / filename;
- class / symbol / function / method;
- test identifier;
- exception/error type;
- meaningful error/diagnostic message.

Code-oriented signals and error-semantic signals are both retained. Each selected signal is an independent query, with the same `candidate_top_k=20`, equal weights, `RRF k=60`, and final Top-10 selection.

Repository BM25 documents include both the repository-relative path tokens and chunk content tokens so filename/path queries can match even when the literal path is absent from source text. Path tokens are not given an additional V1 weight.

### 7. Tokenization and BM25 implementation

L3 V1 uses a DevAgentOps-owned code/log-aware tokenizer before BM25 scoring.

Tokenizer rules:

- lowercase for retrieval matching;
- preserve the normalized compound technical token;
- also split on path separators, `.`, `_`, and `-`;
- split camelCase / PascalCase into subtokens;
- no stemming;
- no stopword removal.

Example:

```text
FooService.java
-> fooservice.java, fooservice, foo, service, java
```

V1 BM25 is local, per-Case, in-process, and ephemeral. The implementation is pinned to:

```text
bm25s == 0.3.10
method = lucene
k1 = 1.5
b  = 0.75
```

These are an untuned implementation baseline, not parameters calibrated on `triage-suite-v1` hidden ground truth.

### 8. Context packing and model-visible order

Retrieval ranking decides **which** chunks are selected. Model-visible packing then removes only literal duplicate exposure:

- exact duplicate chunks are represented once;
- overlapping spans from the same Physical Artifact are coalesced by physical union;
- non-overlapping spans are never bridged across unretrieved gaps;
- spans from different files are never merged;
- no new retrieval slots are backfilled after coalescing.

Example:

```text
1-100 + 81-180 -> 1-180
1-100 + 161-260 -> remain separate
```

Log evidence is serialized in original physical line order. Repository files are ordered by each file's best retrieval rank; spans within a file are serialized by physical line order.

BM25 scores, RRF scores, and retrieval ranks are Trace/debug metadata only. They are not exposed to the model as relevance hints.

### 9. Model-visible runtime input

L3 uses the same shared Task Contract and Structured Triage Report semantics as L1. The runtime input serialization version is distinct, for example:

```text
static_retrieval_runtime_input_v1
```

The model-visible runtime input contains:

- public Case metadata;
- selected/packed Physical Artifact source spans and content;
- source path and physical line range;
- overlapping answer-neutral Canonical Evidence coordinates/IDs needed for evidence references.

It excludes Required Evidence, Expected Answer, previous eval outputs, leaderboard/badcase findings, and all evaluator-only labels.

Like L1, configured L3 performs exact input-token preflight for its single request and does not silently truncate selected evidence. Context infeasibility is an execution failure rather than an unversioned trimming policy.

### 10. Trace and diagnostic attribution

The Runtime records enough retrieval metadata to reproduce and debug evidence acquisition, including:

- retriever component version/fingerprint;
- extracted/selected query signals;
- selected chunk source spans;
- per-query BM25 rank/score for selected chunks;
- fused RRF score/rank;
- packed model-visible spans;
- overlapping Canonical Evidence IDs;
- model-visible byte/token accounting.

Canonical overlap mapping is deterministic and answer-neutral:

```text
retrieved physical span
-> overlapping Canonical Evidence IDs
```

Hidden Required Evidence comparison remains evaluator-side only. A simple `retrieval_evidence_exposure` diagnostic may later report how many Required Evidence IDs overlap model-visible retrieved spans, but it is not a new V1 formal quality metric and must not affect retrieval behavior or parameter tuning.

### 11. Explicit V1 non-goals

L3 V1 does not add:

- embeddings or a vector database;
- Elasticsearch/OpenSearch or another retrieval service;
- neural reranking;
- MMR/diversity reranking;
- LLM-generated retrieval queries;
- AST/language-specific chunking;
- dynamic Top-K or dynamic chunk sizes;
- source-quota redistribution;
- retrieval-result backfill after overlap coalescing;
- formal-suite hidden-ground-truth tuning;
- repair, sandbox execution, test reruns, or adaptive tools.

These may be separate future Treatments only if evidence justifies them.

## Consequences

Positive:

- L1 -> L3 is a comparatively clean evidence-delivery intervention;
- L3 remains clearly distinct from L4 adaptive investigation;
- retrieval behavior is deterministic, local, reproducible, and attributable;
- large logs cannot starve repository evidence slots;
- the baseline is realistic enough to exercise retrieval without becoming a general RAG infrastructure project;
- retrieval traces can distinguish evidence-acquisition failures from model/report-use failures.

Trade-offs:

- fixed lexical heuristics will miss some failure signals;
- fixed source quotas can under-use one pool on some Cases;
- generic line chunking ignores language structure;
- no learned reranker/diversification means V1 is intentionally not an optimized retriever.

These are accepted baseline limitations.

## Supersession and compatibility

This ADR refines ADR 0127's previously abstract L3 definition and supersedes **only** ADR 0118's requirement for a standalone `retrieval_corpus_version` for the fixed `triage-suite-v1` per-Case Physical Artifact corpus.

ADR 0118 remains active for all other boundaries, including:

- Runtime-specific Retrieval chunks remain distinct from Canonical Evidence Units;
- retrieval returns source-faithful Physical Artifact spans;
- repository evidence comes from the frozen Case snapshot, never the current working tree;
- evaluator artifacts and prior eval feedback are forbidden from normal retrieval;
- independently mutable/shared future corpora require explicit identity and leakage controls.

## Verification requirements

Before L3 is considered implemented, deterministic tests must prove at minimum:

- 100/20 chunk boundaries and no cross-file chunks;
- code-aware tokenization behavior;
- signal normalization/dedup/cap/later-first behavior;
- separate log/repo pools and no quota redistribution;
- BM25 Top-20 per query + equal-weight RRF k=60 + deterministic Top-10 selection;
- repository path metadata participates in lexical indexing;
- overlap coalescing never bridges unretrieved gaps or files and never backfills;
- model-visible serialization excludes ranking scores and evaluator labels;
- physical spans map only to answer-neutral Canonical coordinates;
- exactly one configured model request is issued after retrieval;
- exact-token preflight has no silent truncation;
- existing L1/L2/Oracle/L4 behavior and frozen historical identities remain unchanged.
