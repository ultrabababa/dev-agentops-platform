# Require New Condition ID for Condition Drift

Formal evaluation matrix conditions must not reuse the same condition identifier for different effective condition fingerprints. Non-behavior documentation changes may keep the same identifier, but changes to runtime, model configuration, component versions, budgets, repeats, suite, or evaluation method require a new condition identifier so reports, leaderboards, and badcase discussions do not refer to multiple experiment setups with one name.
