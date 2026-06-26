# Limit Leaderboard to Formal Evaluation Runs

DevAgentOps will allow only formal evaluation runs to update the evaluation leaderboard, and leaderboards will be partitioned by evaluation method version rather than merged into one global ranking. Debug runs may appear in trace and development views, but leaderboard results must come from repository-defined evaluation matrix conditions, use frozen components, pass component fingerprint validation, and share the same evaluation method version, evaluation suite version, and model configuration for direct comparison.
