# Version Component Manifest Schemas

V1 component manifests will include a schema version separate from the component version. The schema version identifies the manifest file format and fingerprinting rules, while the component version identifies the frozen prompt, tool, retrieval, skill, sandbox, or MCP contract; unknown schema versions should be rejected rather than guessed so formal evaluation does not compute fingerprints from ambiguous manifests.
