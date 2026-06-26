# Run Eval Doctor Before Formal Evaluation

V1 formal evaluation runner will execute `eval doctor` before running agents, scoring results, or updating reports and leaderboards. Formal evaluation cannot skip this integrity check, while debug workflows may use warning or bypass modes for faster iteration; this preserves leaderboard trust and catches configuration, schema, fingerprint, and leakage problems before model cost is incurred.
