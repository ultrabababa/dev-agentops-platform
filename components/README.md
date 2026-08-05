# Component registry

This directory is the repository-managed registry for frozen, behavior-affecting
agent components. Draft manifests may live anywhere outside `components/frozen/`.
The freeze command validates a draft, copies it into `components/frozen/`, and
adds its immutable version and canonical fingerprint to `registry.json`.

For the Evaluation Matrix rules, the two-layer identity model, and the exact
boundary between structural and formal validation, see
[`docs/evaluation/evaluation-matrix-and-component-registry.md`](../docs/evaluation/evaluation-matrix-and-component-registry.md).

V1 supports these component types:

- `prompt`: required `template`; optional `variables`.
- `tool_registry`: required `tools`, a list of tool contract objects.
- `retriever_config`: required `strategy` and `settings`.
- `tool_policy`: required `rules`; optional `default_action`.
- `mcp_server_set`: required `servers`, a list of server contract objects.
- `skill_registry`: required `skills`, a list of skill contract objects.

Unknown behavior fields are rejected. Empty lists and a `none` retrieval strategy
support honest `none_v1` placeholders for deferred MCP and skill capabilities.

A schema-version-1 draft manifest has a strict envelope:

```json
{
  "schema_version": "1",
  "component_type": "prompt",
  "component_version": "draft",
  "behavior": {
    "template": "Diagnose the failure using evidence from {log}."
  },
  "metadata": {
    "notes": "Review context that does not affect the fingerprint."
  }
}
```

All behavior-affecting configuration belongs under `behavior`. Author, notes,
timestamps, and other review-only values belong under `metadata`. The canonical
schema version 1 fingerprint covers only the canonicalized `behavior` object; it
ignores JSON formatting, key order, component metadata, and review metadata.
Draft manifests may omit `component_version` or set it to `draft`; freezing writes
the requested immutable version into the frozen manifest and registry record.

Validate and freeze a draft from the repository root:

```bash
devagentops component validate --manifest components/drafts/prompt.json
devagentops component freeze \
  --manifest components/drafts/prompt.json \
  --registry components/registry.json \
  --version triage-prompt-v1
```

Formal matrix validation must receive the registry explicitly:

```bash
devagentops eval doctor \
  --matrix path/to/evaluation-matrix.json \
  --registry components/registry.json
```

With `--registry`, `eval doctor` rejects draft and missing versions, reloads every
registered frozen manifest, recomputes its fingerprint, and fails on version
pollution. The normal command requires `--registry`; legacy, non-formal matrix
structure checks must opt in explicitly with `--structural-only`.

The validated component fingerprints become part of the formal condition
fingerprint. Matrix key `retriever` maps to registry type `retriever_config` for
Issue #4 compatibility; a condition cannot declare both aliases. Model
configuration remains a Matrix field and is not stored in this registry.
