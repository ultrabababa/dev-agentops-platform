# Component Versioning and Run Manifests

## Status

Accepted.

## Context

Prompt, tool schema, retriever configuration, sandbox policy, and MCP server set changes can alter evaluation results even when runtime code is unchanged. V1 needs enough version discipline for badcase analysis and regression without building a full release system.

## Decision

V1 will store a run manifest for each run, including code revision, effective condition, component versions, and component fingerprints. Frozen components are recorded in a repository component registry grouped by component type. Draft components may change freely but cannot enter formal evaluation matrix conditions. A referenced component version is immutable; the same version with a different fingerprint is version pollution.

## Alternatives Considered

- Hash the whole repository only. This is too coarse and cannot identify prompt, tool, retriever, or policy changes.
- Use GitHub Releases for every component change. This is too heavy for prompt and tool iteration.
- Let component version IDs be mutable labels. This breaks reproducibility and badcase analysis.

## Consequences

Formal evaluation can fail fast when component identity is polluted. Developers can still iterate quickly with draft components and debug runs before freezing a new component version.

## Implementation Notes

- Component fingerprints are computed from canonicalized behavior-affecting manifest fields, not raw file bytes.
- Manifest schemas declare behavior-affecting fields and metadata fields.
- Freeze-time validation writes registry records; formal evaluation revalidates manifests and fingerprints before running.
- Component registry stores only frozen components.
- Model configuration is recorded in conditions and run manifests, but not in the component registry.

## Consolidates

Micro ADRs: `0018`, `0019`, `0020`, `0021`, `0022`, `0038`, `0040`, `0041`, `0042`, `0043`, `0044`.
