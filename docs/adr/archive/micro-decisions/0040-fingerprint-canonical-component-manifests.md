# Fingerprint Canonical Component Manifests

V1 component fingerprints will be computed from canonicalized behavior-affecting manifest content rather than raw file bytes. Parsing manifests, excluding explicitly non-behavior metadata, sorting keys, normalizing representation, and hashing canonical JSON avoids fingerprint churn from comments, field order, or formatting while still detecting changes to prompts, tool schemas, retrieval settings, skill registries, sandbox policies, and MCP server sets.
