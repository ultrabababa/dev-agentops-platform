# Use a Thin Docker Compose Setup for V1

V1 will include Docker Compose for one-command local demo startup, but it will only run the FastAPI backend and React/Vite dashboard. PostgreSQL, Redis, queue workers, and vector databases are deferred until V2 so the V1 infrastructure matches the SQLite-first, lightweight retrieval, and single-user evaluation scope.
