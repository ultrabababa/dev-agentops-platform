from pathlib import Path

from fastapi import FastAPI

from devagentops import __version__
from devagentops.config import DEFAULT_DATABASE_PATH
from devagentops.storage import inspect_database


def create_app(database_path: Path) -> FastAPI:
    app = FastAPI(title="DevAgentOps", version=__version__)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/version")
    def version():
        return {"version": __version__}

    @app.get("/storage/status")
    def storage_status():
        status = inspect_database(database_path)
        return status.as_dict()

    return app


app = create_app(DEFAULT_DATABASE_PATH)
