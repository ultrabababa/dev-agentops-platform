"""Executable HTTP contract for Lesson 0005."""

from fastapi.testclient import TestClient

from learning_exercises.lesson_0005_health_version import app


client = TestClient(app)


def test_health_reports_process_is_alive():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_reports_package_version():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "0.1.0"}
