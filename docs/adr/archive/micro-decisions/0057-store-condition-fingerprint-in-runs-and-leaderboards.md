# Store Condition Fingerprint in Runs and Leaderboards

Formal run manifests and leaderboard records will store the condition fingerprint alongside condition identity, matrix identity, matrix version, and effective condition details. This lets DevAgentOps distinguish stable condition results from condition drift, so the same condition identifier with a different effective setup cannot be silently mixed into a comparable leaderboard row.
