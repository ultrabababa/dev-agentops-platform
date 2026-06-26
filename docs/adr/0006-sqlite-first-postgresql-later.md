# Use SQLite First with a PostgreSQL Migration Path

V1 will persist cases, runs, trace events, reports, and eval results in SQLite through SQLAlchemy or SQLModel with Alembic migrations. SQLite keeps the local eval and demo loop simple, while the repository and migration boundaries preserve a path to PostgreSQL when DevAgentOps needs concurrent runs, long-lived API service behavior, richer trace analysis, JSONB-heavy queries, or pgvector-backed retrieval.
