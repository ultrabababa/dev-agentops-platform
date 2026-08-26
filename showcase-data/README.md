# Public Evaluation Explorer data

This directory is the immutable public input for the read-only Evaluation
Explorer. `catalog.json` maps twelve real formal Run IDs to nine sanitized SQLite
snapshots. Metric values are deliberately absent from the catalog.

Data authority:

- SQLite snapshots: Run/Sample state, manifests, reports, scores, aggregates,
  sanitized Trajectory, and Trace;
- `docs/evaluation/milestones/*-results-*.json`: experiment-specific diagnostics;
- `evaluation/suites/triage-v1/`: frozen public-safe Suite/Case metadata.

The original ignored `.devagentops` databases are internal audit/replay data and
must never be copied into this directory. Build each destination explicitly with:

```sh
PYTHONPATH=src python -m devagentops.explorer.sanitize \
  /absolute/path/to/private-source.sqlite3 \
  showcase-data/databases/public-name.sqlite3 \
  --run-id UUID
```

Pass `--run-id` once for each retained Run when one public database contains
multiple cataloged Runs. The destination must not already exist. Generation
opens the source read-only, filters to the requested Runs, sanitizes Trajectory
and Trace, recomputes message hashes, vacuums the copy, and runs leakage
validation. Source paths are operator inputs and are never a runtime dependency.

Validate a snapshot without exposing sensitive values:

```sh
PYTHONPATH=src python -c \
  'from devagentops.explorer.sanitize import validate_public_database; import sys; print(validate_public_database(sys.argv[1]))' \
  showcase-data/databases/public-name.sqlite3
```

See [ADR 0131](../docs/adr/0131-public-evaluation-explorer-data-boundary.md).
