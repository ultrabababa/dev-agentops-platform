# Use an OpenAI-Compatible LLM Provider Boundary

V1 will define a small provider-neutral LLM client interface, but the first concrete provider will use an OpenAI-compatible chat/completions-style API configured through model, base URL, and API key. This gives enough portability across compatible hosted or local gateways without spending V1 effort on multiple vendor SDKs, provider-specific routing, or fallback behavior before the triage runtime and eval loop are stable.
