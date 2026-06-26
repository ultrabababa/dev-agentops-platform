# Check Evaluation Artifact Leakage by Paths

V1 `eval doctor` will check for evaluation artifact leakage using path and configuration rules rather than complex semantic analysis. Retrieval sources and project knowledge references must not point to expected answers, evaluation reports, leaderboard data, badcase reviews, debug findings, or other evaluation artifacts; deeper semantic leakage detection is deferred until concrete contamination problems justify it.
