# Defer Real MCP Integration

V1 will not connect to real MCP servers, but evaluation conditions and run manifests will still carry an MCP server set version such as `none_v1`. This keeps the comparison contract ready for later MCP ablations or candidate conditions while avoiding V1 complexity around server lifecycle, tool discovery, auth, schema drift, trace normalization, and external failure modes.
