# ADR 0131: Public Evaluation Explorer Data Boundary

## Status

Accepted and implemented for Evaluation Explorer Phase 1.

## Context

Formal evaluation databases are internal audit/replay records. In particular, L4
trajectory messages preserve provider-returned thinking, reasoning continuation
fields, opaque provider state, and provider-specific usage details. That fidelity
is necessary for internal debugging and replay, but those raw databases are not a
safe public website input.

The public Explorer must still show real Run, Case, Sample, Report, Evidence,
Trajectory, Trace, metric, and provenance records. Copying official metrics into
a dashboard-specific schema would create a second authority and make the public
story drift from the formal evaluation evidence.

## Decision

### Internal evidence and public observability are separate surfaces

The ignored `.devagentops` databases remain the full internal replay/audit
surface. They are never committed and their persistence semantics remain
unchanged.

`showcase-data/databases/` contains deterministic, public-safe SQLite snapshots.
Each snapshot is produced from a source opened read-only, retains the existing
formal evaluation schema, and contains only cataloged formal Run IDs. The source
database is never mutated.

### Deterministic sanitization is mandatory

Trajectory messages use a role-specific allowlist. Public copies keep visible
content, safe ToolCall/ToolResult fields, stop reasons, returned model identity,
and input/output/total token counts. They remove hidden thinking/reasoning,
provider fields, response/provider request identifiers, encrypted or opaque
continuation state, and credential-like content. The sanitized message SHA is
recomputed over canonical JSON.

Trace JSON is sanitized independently because Trace also contains provider
fields. The public API then applies another explicit field allowlist. Sanitizing
SQLite alone is not considered a sufficient browser boundary.

Every generated database is validated without printing sensitive values.
Validation reports only key names, counts, paths, and row identities, and fails
on forbidden private keys or obvious credential patterns.

### One read-only multi-database catalog

`showcase-data/catalog.json` maps editorial experiment roles to the twelve real
formal Run IDs across nine public SQLite files. `EvaluationCatalog` opens these
files with SQLite `mode=ro`, `immutable=1`, and `query_only=ON`; it rejects
missing databases, duplicate Run IDs, catalog/physical mismatches, and
uncataloged runs.

The catalog contains stages, roles, representative-condition mappings, and
comparison groups. It does not duplicate metric values.

### Authority remains split by evidence type

- SQLite is authoritative for Run/sample state, manifests, reports, scores,
  Case/Suite/Failure Type aggregates, sanitized Trajectory, Trace, and
  provenance identities.
- Checked-in milestone JSON is authoritative for fixed-output canonicalization
  replay, L4 Runtime-efficiency/replication observations, and L3
  acquisition/utilization diagnostics.
- Frozen Suite/Case artifacts are authoritative for public-safe Case metadata,
  Agent-visible source provenance, and canonical coordinates.

The API never asks React to compute or invent official metrics and never returns
raw manifest, trajectory, or Trace JSON.

### V1 backend remains FastAPI and SQLite

The Explorer adds GET-only routes under `/api`. Existing health, version, and
storage endpoints remain unchanged. V1 adds no POST/PUT/PATCH/DELETE behavior,
no online evaluation or Agent execution, and no database editing.

There is no Dashboard persistence model and no Supabase, PostgreSQL, Redis,
background worker, WebSocket, authentication, or account system in V1.

## Consequences

- Public users can inspect genuine frozen evaluation evidence without receiving
  hidden provider reasoning or private continuation state.
- Internal audit/replay fidelity remains intact because sanitization is a derived
  copy operation.
- Schema v5 historical databases that lack trajectory storage remain valid;
  trajectory availability is detected per Run/Case/Repeat rather than inferred
  from a capability label.
- Official experiment interpretation remains coupled to checked-in machine
  artifacts instead of application literals.
- Updating public data requires regenerating, validating, reviewing, and
  replacing immutable snapshots; the runtime application never depends on the
  ignored private source paths.

## Non-goals

Phase 1 does not implement the final React dashboard, bilingual editorial copy,
architecture diagrams, search, badcase writes, authentication, online execution,
or Phase 2 interaction design.

## Related Decisions

- [ADR 0006: SQLite First, PostgreSQL Later](0006-sqlite-first-postgresql-later.md)
- [ADR 0008: React/Vite Dashboard](0008-react-vite-dashboard.md)
- [ADR 0121: CLI, Dashboard, Reports, and Storage](0121-cli-dashboard-reports-and-storage.md)
- [ADR 0123: Case Provenance and Sanitization](0123-case-provenance-and-sanitization.md)
- [ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md)
