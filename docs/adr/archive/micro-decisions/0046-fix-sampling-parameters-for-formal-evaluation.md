# Fix Sampling Parameters for Formal Evaluation

V1 formal evaluation will use low-randomness model settings by default, such as temperature zero, top_p one, and a fixed seed when the provider supports it. These settings reduce output variability for runtime, prompt, tool, and retrieval comparison, but run manifests must still record provider, model, version or snapshot, and inference parameters because LLM outputs are not guaranteed to be fully deterministic.
