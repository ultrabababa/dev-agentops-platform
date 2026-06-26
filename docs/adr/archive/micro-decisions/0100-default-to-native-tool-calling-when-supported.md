# Default to Native Tool Calling When Supported

V1 will default to provider-native tool calling when the configured OpenAI-compatible provider supports it. A strict JSON action fallback remains available for providers without native tool calling and for explicit protocol ablations, but it is not the preferred default because native tool calling provides stronger schema alignment, parameter handling, and structured trace behavior.
