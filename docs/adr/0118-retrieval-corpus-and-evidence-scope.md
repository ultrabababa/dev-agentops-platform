# Retrieval Corpus and Evidence Scope

## Status

Accepted. ADR 0130 supersedes only the requirement for a standalone `retrieval_corpus_version` for L3 `static_retrieval` over the fixed per-Case Physical Artifact corpus in `triage-suite-v1`. All other corpus, leakage, frozen-snapshot, source-span, and Canonical Evidence boundaries in this ADR remain active.

## Context

Retrieval affects triage quality, but formal evaluation must avoid answer leakage and drift from mutable local files or previous eval artifacts.

## Decision

V1 will version retriever behavior separately from retrieval corpus content. For a Formal Case, an independently versioned Runtime Retrieval Chunker derives index chunks from allowed Physical Artifacts; static retrieval returns physical source spans, which are mapped to overlapping Canonical Evidence IDs for identity, citation, and measurement. Canonical Units are not mandatory Retrieval chunks. Formal evaluation may also retrieve separately controlled project knowledge, but not expected answers, leaderboard results, badcase reviews, debug findings, or previous evaluation reports. Repository evidence comes from frozen Case or corpus snapshots, not the current working tree.

For the current `triage-suite-v1` L3 condition, ADR 0130 narrows the identity rule: the corpus is fixed to `case_physical_artifacts`, Case/Suite fingerprints already identify that content, and no redundant standalone `retrieval_corpus_version` is added. A separately mutable/shared future corpus still requires explicit identity.

## Alternatives Considered

- Let the agent retrieve previous badcases or expected answers. This leaks evaluation feedback.
- Combine retriever and corpus into one version. This makes evidence hit changes hard to attribute.
- Index the current repository during formal evaluation. This makes results drift as DevAgentOps code changes.

## Consequences

Retrieval improvements are attributable to strategy, corpus, or evidence changes. Formal evaluation measures triage behavior rather than answer memorization.

## Implementation Notes

- `retriever_version` covers chunking, algorithm, index/query, top-k/reranking, and other behavior-affecting configuration.
- For `triage-suite-v1` L3, corpus identity is carried by the frozen Case/Suite fingerprints rather than a standalone `retrieval_corpus_version`.
- If future retrieval introduces project knowledge, shared content, or another independently versioned corpus, restore an explicit corpus identity for that Treatment.
- Runtime traces preserve retrieved physical spans and overlapping Canonical IDs; the formal Evidence Hit attribution rule is calibrated separately and cannot default to arbitrary overlap.
- Project knowledge may include SOPs, runbooks, architecture notes, dependency policy, and testing conventions.
- `eval doctor` checks path/configuration-level leakage from evaluation artifacts.

## Consolidates

Micro ADRs: `0075`, `0076`, `0077`, `0078`, `0079`, `0080`, `0090`.
