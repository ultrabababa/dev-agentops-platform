# Record Tool Call Protocol

V1 will record the tool call protocol in evaluation conditions and run manifests. Provider-native tool or function calling is preferred when the configured model provider supports it, while a strict validated JSON action fallback preserves portability for OpenAI-compatible providers without native tool calling; the protocol affects parameter validity, stability, trace shape, and therefore must be explicit in comparisons.
