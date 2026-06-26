# Version Evaluation Methods for Fair Comparison

DevAgentOps will version the evaluation method separately from runtime variants and evaluation conditions. Scores may be compared directly only when they share the same evaluation method version; when the evaluation method changes, such as moving scoring or reporting into Langfuse, the project must rerun selected anchor conditions instead of merging old and new leaderboards. This keeps historical results useful while making metric, scorer, judge, and reporting changes explicit.
