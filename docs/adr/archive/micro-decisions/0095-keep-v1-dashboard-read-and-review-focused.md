# Keep V1 Dashboard Read and Review Focused

V1 dashboard will not trigger formal or debug runs. It will focus on viewing traces, evaluation reports, leaderboards, badcases, and badcase review, while CLI commands remain responsible for running evaluations; dashboard-triggered runs are deferred because they require job orchestration, cancellation, progress state, error recovery, concurrency handling, and credential management.
