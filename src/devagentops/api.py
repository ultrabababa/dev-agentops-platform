import os
from pathlib import Path

from fastapi import FastAPI

from devagentops import __version__
from devagentops.config import DEFAULT_DATABASE_PATH
from devagentops.storage.database import inspect_database


DEFAULT_SHOWCASE_CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "showcase-data" / "catalog.json"
)
SHOWCASE_CATALOG_ENV = "DEVAGENTOPS_SHOWCASE_CATALOG_PATH"


def configured_showcase_catalog_path() -> Path | None:
    configured = os.environ.get(SHOWCASE_CATALOG_ENV)
    if configured is not None:
        if not configured.strip():
            raise RuntimeError(f"{SHOWCASE_CATALOG_ENV} is configured but empty")
        path = Path(configured).expanduser().resolve(strict=False)
        if not path.is_file():
            raise RuntimeError(
                f"{SHOWCASE_CATALOG_ENV} does not point to a catalog file: {path}"
            )
        return path
    if (
        DEFAULT_SHOWCASE_CATALOG_PATH.is_file()
        and (DEFAULT_SHOWCASE_CATALOG_PATH.parent / "databases").is_dir()
    ):
        return DEFAULT_SHOWCASE_CATALOG_PATH
    return None


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
    explorer_catalog_path=configured_showcase_catalog_path(),
)
