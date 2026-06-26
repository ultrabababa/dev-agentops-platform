# Record Run Manifest with Component Fingerprints

V1 will persist a run manifest for each triage run that records the code revision plus human-readable versions and content fingerprints for behavior-affecting components such as prompts, tool schemas, retrieval configuration, skill registry, sandbox policy, and MCP server set. The code revision identifies the implementation used for the run, while component fingerprints make prompt, tool, retrieval, policy, and integration changes visible without treating every repository file change as an AgentOps behavior change.
