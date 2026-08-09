# Offline Case Schema V2 Physical Artifacts and Canonical Evidence

## Status

Accepted.

## Context

Offline Case Schema V1 represents logs asymmetrically from repository evidence. A frozen `raw.log` is the physical log source and `log-chunks.json` contains evidence units, but repository content exists only inside `repository-evidence.json`. That file is simultaneously treated as the repository material an Agent can inspect and the Canonical Evidence used for citation and scoring.

This conflates the physical repository Investigation Workspace with Evaluator coordinates, encourages curator-localized evidence packages, and prevents source-span integrity from being verified against an independently frozen repository snapshot. V1 also stores Required/Optional Evidence IDs inside Expected Answer, combining Evidence Ground Truth with Diagnosis Ground Truth.

Freezing 20 Formal Cases under that model and migrating them later would repeat package construction, provenance review, evidence review, and fingerprint validation. The structural boundary must therefore be corrected before Issue #15 freezes the first Formal Suite.

## Decision

Offline Case Schema V2 will separate three storage and trust layers:

```text
<case-id>/
├── case.json
├── physical-artifacts/
│   ├── raw.log
│   ├── repository-manifest.json
│   └── repository/
├── canonical-evidence/
│   ├── log-units.json
│   └── repository-units.json
└── evaluator/
    ├── required-evidence.json
    └── expected-answer.json
```

Issue #22 冻结并实现了 exact envelope；以下职责和契约现在由 V2-only Loader 强制执行。

### Physical Artifacts

`physical-artifacts/raw.log` is the complete or naturally bounded frozen CI/test log. `physical-artifacts/repository/` contains bounded repository files derived from the exact failing or otherwise relevant upstream revision and preserves their source-relative paths. When source artifacts contain credentials, tokens, private identifiers, or other disallowed data, they may undergo Human-reviewed, semantics-preserving sanitization before being frozen in the Case Package. Sanitization must not change the failure's causal semantics.

The provenance chain is:

```text
upstream repository and exact revision
        -> optional Human-reviewed semantics-preserving sanitization
        -> frozen Physical Artifact in the Case Package
        -> Canonical Evidence source spans and resolved hashes
        -> Case fingerprint
```

`repository-manifest.json` explicitly declares the real upstream repository identity, exact revision identity, snapshot membership, and each frozen file's path, SHA-256, and byte size. The per-file integrity fields describe the frozen Physical Artifact after any allowed sanitization; they do not require its bytes to equal the upstream commit bytes. Provenance and sanitization metadata must record which allowed transformations occurred and their Human review status. Formal membership is manifest-driven; loaders must not silently discover snapshot files by directory scanning. Manifest identity, declared frozen-file integrity, and resolved frozen content participate in deterministic Case fingerprint coverage.

For the first Formal Suite, the Case Evidence Universe contains only the physical log and bounded exact-revision repository snapshot. Project Knowledge is not a Schema V2 Case artifact.

### Canonical Evidence

Canonical Log and Repository Units are coordinates over the frozen Physical Artifacts in the Case Package, not independent copies of source truth or a curator-selected high-value subset. Every unit has a stable answer-neutral Evidence ID, a controlled source path, a machine-readable source span, and a hash of the resolved frozen content.

The current Schema V2 Loader enforces only the declared-unit integrity boundary: controlled source paths, manifest-declared repository membership, valid positive in-bounds line spans, kind/ID shape and uniqueness, exact resolved-content hashes, and Ground Truth references to known Canonical IDs. It does **not** currently prove that the declared units cover every physical line, have no gaps/overlaps, or comply with a suite-shared Canonicalization Profile.

Complete Formal text coverage, no gaps/overlaps, answer-neutral boundaries, and independence from failure lines, fixes, Required Evidence labels, or curator conclusions are Case Construction/Human Review invariants. Before bulk Formal Case construction, a deterministic Canonicalization Profile generator/validator or equivalent machine validation must enforce those invariants and Profile compliance. This requirement does not reopen or expand Issue #22 in the current documentation/calibration phase.

Formal Cases will use a shared versioned `Canonicalization Profile v1`. Its repository-text candidate starts at line 1 and uses contiguous, non-overlapping fixed-`N` windows with a possibly shorter final unit and 100% coverage. B04 currently uses `N=100`, but one calibration Case is insufficient to freeze that parameter for the Suite. Profile calibration must precede bulk Case construction.

Canonicalization does not define Runtime Retrieval Chunking. A Retrieval Runtime may independently chunk the Physical Artifacts using versioned size, overlap, embedding, index, top-k, and reranking parameters, then map retrieved physical spans to overlapping Canonical Evidence IDs. Canonical Units remain stable identity, citation, and measurement coordinates; they are not mandatory Retrieval index chunks.

### Trusted Evaluator Artifacts

The entire `evaluator/` directory belongs to the Trusted Evaluator boundary.

`required-evidence.json` is the only Evidence Ground Truth source. It stores the Human-reviewed Required and Optional Canonical Evidence IDs used by Retrieval Evidence Hit, Report Evidence Hit, Oracle construction, and evidence review.

`expected-answer.json` stores Diagnosis Ground Truth such as Primary/Acceptable Failure Type, Expected Summary, Expected Root Cause, and Recommended Action. It does not duplicate Required/Optional Evidence IDs.

No permanent `oracle-evidence.json` or pre-materialized perfect-content pack is stored. The Oracle Pack is deterministically derived at runtime by resolving `required-evidence.json` through Canonical Evidence coordinates to Physical Artifact content. The model receives normal Evidence IDs and resolved source-faithful content, but no evaluator filenames, labels, answer fields, reasoning, or selection rationale.

### Visibility and Fingerprints

Directory layout provides a strong physical trust-boundary convention. Actual model/tool visibility is enforced and fingerprinted by the Evidence Acquisition Condition and Runtime; not every runtime receives identical access.

Case identity must cover the V2 manifest, frozen Physical Artifact membership and content, upstream repository/revision identity, per-file integrity, Canonical Evidence definitions and resolved frozen-content hashes, Trusted Evaluator artifacts, provenance, sanitization metadata, and review state. Exact-revision provenance does not imply byte equality with upstream when reviewed semantics-preserving sanitization is recorded. Suite fingerprints continue to compose verified Case fingerprints.

## Alternatives Considered

- Keep Schema V1 and document Human Review rules. This cannot establish an independent physical repository source or machine-verifiable source-span mapping.
- Store canonical repository content as duplicated text. This creates a second fact source that can drift from the physical snapshot.
- Store a permanent Oracle evidence pack. This duplicates Required Evidence ground truth and can drift from source artifacts.
- Add Project Knowledge to every Case. It changes a runtime/retrieval input into mandatory Case data and confounds future ablations.
- Finish 20 V1 packages and migrate later. This knowingly creates avoidable reconstruction and Human Review cost.

## Consequences

Positive consequences:

- ReAct can investigate a real bounded physical repository workspace.
- Retrieval, traces, citations, scoring, and Oracle use the same source-resolved coordinates.
- Evidence and Diagnosis Ground Truth have one source of truth each.
- Physical, canonical, and evaluator-only integrity can be validated and fingerprinted independently.
- Runtime chunking experiments can vary without changing Case identity or evaluator coordinates.

Tradeoffs:

- Schema V2 loader, Doctor support, fixtures, fingerprints, and compatibility behavior must be implemented by [Issue #22](https://github.com/ultrabababa/dev-agentops-platform/issues/22) before Formal Case freeze.
- Case construction and review become more explicit.
- Existing Batch-1 Schema V1 packages remain calibration drafts and must not be Human-frozen as Formal Packages.

Issue #15 must not construct the remaining 15 packages under Schema V1. B04 has been rebuilt under Schema V2 and passed Human Review. Before construction scales, 2–3 already-selected structurally different Cases must calibrate `Canonicalization Profile v1`; if the frozen parameters differ from B04's current local rule, B04 Canonical coordinates and dependent Evidence IDs/fingerprint must be rebuilt uniformly while its Physical Artifacts remain unchanged.

Schema V1 Loader 已明确退役：缺失或类型错误的 `case_schema_version` 是 `invalid_case_manifest`，显式非 `"2"` 版本是 `unsupported_case_schema_version`。Tiny fixture 已原地迁移到 V2；不提供双版本分派、mixed-schema Suite 或 V1 migration framework。Issue #15 的五个 V1 calibration drafts 不在 Issue #22 中迁移。

## Non-Decisions

- Runtime、retrieval、tools 与 Oracle Runner 仍不属于本 ADR/Issue #22；V2 Loader、Doctor、scorer integration 与 public leakage boundary 已实现。
- It does not freeze `Canonicalization Profile v1`, `N=100`, or a corpus-size threshold; calibration and a separate Human decision are required.
- It does not define Runtime Retrieval Chunking or require Runtime chunks to equal Canonical Units.
- It does not add Project Knowledge to Schema V2.
- It does not require a migration framework unless implementation proves one necessary.
- It does not modify the five Failure Types, scoring formulas, or diagnosis-only product boundary.

## Refines

ADRs: `0115`, `0118`, `0122`, `0123`, `0124`, `0125`.
