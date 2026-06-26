# Declare Behavior-Affecting Manifest Fields

V1 component manifest schemas will explicitly declare which fields affect behavior and therefore participate in component fingerprinting. Metadata such as author, timestamps, notes, and changelog entries may be stored for review context but must be excluded from fingerprints, while prompt templates, tool descriptions and schemas, retrieval settings, skill registry contracts, sandbox policies, and MCP tool manifests must be included when they affect agent behavior.
