from pathlib import Path

from fastapi import FastAPI

from devagentops import __version__
from devagentops.config import DEFAULT_DATABASE_PATH
from devagentops.storage.database import inspect_database


DEFAULT_SHOWCASE_CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "showcase-data" / "catalog.json"
)


def create_app(
    database_path: Path,
    *,
    explorer_catalog_path: Path | None = None,
) -> FastAPI:
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

    if explorer_catalog_path is not None:
        from devagentops.explorer.router import create_explorer_router
        from devagentops.explorer.service import ExplorerService

        app.include_router(
            create_explorer_router(ExplorerService(explorer_catalog_path))
        )

    return app


app = create_app(
    DEFAULT_DATABASE_PATH,
    explorer_catalog_path=(
        DEFAULT_SHOWCASE_CATALOG_PATH
        if DEFAULT_SHOWCASE_CATALOG_PATH.is_file()
        and (DEFAULT_SHOWCASE_CATALOG_PATH.parent / "databases").is_dir()
        else None
    ),
)
