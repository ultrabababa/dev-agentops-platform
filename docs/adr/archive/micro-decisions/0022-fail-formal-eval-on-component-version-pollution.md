# Fail Formal Evaluation on Component Version Pollution

Formal evaluation runs will fail fast when a component version resolves to a fingerprint that differs from the historical fingerprint for that version. Debug runs may warn instead so prompt, tool, retrieval, policy, or runtime experimentation remains lightweight, but leaderboard, regression, and badcase conclusions must not be produced from polluted component versions.
