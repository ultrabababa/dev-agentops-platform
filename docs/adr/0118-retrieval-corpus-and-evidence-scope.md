# Retrieval Corpus and Evidence Scope

## Status

Accepted.

## Context

Retrieval affects triage quality, but formal evaluation must avoid answer leakage and drift from mutable local files or previous eval artifacts.

## Decision

V1 will version retriever behavior separately from retrieval corpus content. For a Formal Case, an independently versioned Runtime Retrieval Chunker derives index chunks from allowed Physical Artifacts; static retrieval returns physical source spans, which are mapped to overlapping Canonical Evidence IDs for identity, citation, and measurement. Canonical Units are not mandatory Retrieval chunks. Formal evaluation may also retrieve separately controlled project knowledge, but not expected answers, leaderboard results, badcase reviews, debug findings, or previous evaluation reports. Repository evidence comes from frozen Case or corpus snapshots, not the current working tree.

## Alternatives Considered

- Let the agent retrieve previous badcases or expected answers. This leaks evaluation feedback.
- Combine retriever and corpus into one version. This makes evidence hit changes hard to attribute.
- Index the current repository during formal evaluation. This makes results drift as DevAgentOps code changes.

## Consequences

Retrieval improvements are attributable to strategy, corpus, or evidence changes. Formal evaluation measures triage behavior rather than answer memorization.

## Implementation Notes

- `retriever_version` covers chunking, algorithm, index/query, top-k/reranking, and other behavior-affecting configuration.
- `retrieval_corpus_version` covers the allowed Physical Artifact snapshot or separately controlled project-knowledge content from which Runtime chunks are derived.
- V1 defaults to per-case repository evidence snapshots, with future support for shared corpus references.
- Runtime traces preserve retrieved physical spans and overlapping Canonical IDs; the formal Evidence Hit attribution rule is calibrated separately and cannot default to arbitrary overlap.
- Project knowledge may include SOPs, runbooks, architecture notes, dependency policy, and testing conventions.
- `eval doctor` checks path/configuration-level leakage from evaluation artifacts.

## Consolidates

Micro ADRs: `0075`, `0076`, `0077`, `0078`, `0079`, `0080`, `0090`.
