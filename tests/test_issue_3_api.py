from pathlib import Path

from fastapi.testclient import TestClient

from devagentops import __version__
from devagentops.api import app, create_app
from devagentops.cli import main
from devagentops.storage import initialize_database

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version() -> None:
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": __version__}


def test_storage_status_reports_missing_database_without_creating_it(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "missing" / "devagentops.db"
    client = TestClient(create_app(database_path))

    response = client.get("/storage/status")

    assert response.status_code == 200
    assert response.json()["exists"] is False
    assert database_path.exists() is False
    assert database_path.parent.exists() is False


def test_storage_status_reports_initialized_database(tmp_path: Path) -> None:
    database_path = tmp_path / "devagentops.db"
    expected_status = initialize_database(database_path)

    client = TestClient(create_app(database_path))
    response = client.get("/storage/status")

    assert response.status_code == 200
    assert response.json() == expected_status.as_dict()


def test_default_api_reads_database_initialized_by_cli(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["db", "init"]) == 0
    capsys.readouterr()

    response = client.get("/storage/status")

    assert response.status_code == 200
    assert response.json()["initialized"] is True
    assert response.json()["path"] == str(
        (tmp_path / ".devagentops" / "devagentops.db").resolve()
    )
