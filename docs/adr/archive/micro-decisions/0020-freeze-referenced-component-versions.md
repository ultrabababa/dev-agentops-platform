# Freeze Referenced Component Versions

Component versions referenced by a run manifest or evaluation condition will be treated as immutable. If a prompt, tool schema, retrieval configuration, skill registry, sandbox policy, or MCP server set changes behavior, it must receive a new component version; the same version with a different fingerprint is considered version pollution and should be rejected or highlighted during evaluation.
