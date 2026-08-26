from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devagentops.api import configured_showcase_catalog_path, create_app


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "showcase-data" / "catalog.json"
L4 = "d6fee1ba-ddd2-4ed3-ae2f-625603de5fef"
L3 = "a9d5bce2-d635-4573-baf1-d26c391fedf8"
SEQUENTIAL = "b6ad2a0f-1b40-49e2-8ce6-28b14f8b2df8"
BATCH = "d76ac5ca-22a3-4c67-acf3-c33bba68f0d5"
CASE = "bugswarm-traccar-170287308"
FORBIDDEN = {
    "thinking", "reasoning_content", "reasoning_details", "reasoning",
    "encrypted_content", "continuation_state", "provider_state", "provider_fields",
    "response_id", "provider_request_id",
}


def _client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(tmp_path / "local.db", explorer_catalog_path=CATALOG)
    )


def _keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _keys(child)


def test_every_explorer_endpoint_returns_public_data(tmp_path: Path) -> None:
    client = _client(tmp_path)
    paths = [
        "/api/overview",
        "/api/conditions",
        "/api/conditions/L4",
        "/api/experiments/evolution",
        "/api/runs",
        f"/api/runs/{L4}",
        f"/api/runs/{L4}/cases",
        f"/api/runs/{L4}/cases/{CASE}/0",
        f"/api/runs/{L4}/cases/{CASE}/0/trajectory",
        f"/api/runs/{L4}/cases/{CASE}/0/trace",
        "/api/cases",
        f"/api/cases/{CASE}",
        "/api/comparisons",
        f"/api/compare?run_a={SEQUENTIAL}&run_b={BATCH}",
    ]

    responses = [client.get(path) for path in paths]

    assert all(response.status_code == 200 for response in responses), [
        (path, response.status_code, response.text)
        for path, response in zip(paths, responses)
        if response.status_code != 200
    ]


def test_overview_and_conditions_preserve_frozen_semantics(tmp_path: Path) -> None:
    client = _client(tmp_path)

    overview = client.get("/api/overview").json()
    conditions = client.get("/api/conditions").json()

    assert overview["benchmark"] == {
        "case_count": 20,
        "repeats_per_case": 3,
        "samples_per_formal_run": 60,
        "failure_type_count": 5,
    }
    assert overview["representative_conditions"]["L3"]["run_id"] == L3
    assert [item["condition"] for item in conditions] == ["L1", "L2", "L3", "L4", "Oracle"]
    assert next(item for item in conditions if item["condition"] == "Oracle")["runtime_variant"] == "model_one_shot"
    l3 = next(item for item in conditions if item["condition"] == "L3")
    assert set(l3["formal_metric_vector"]) == {
        "execution_coverage",
        "failure_type_exact_match",
        "report_evidence_hit_rate",
        "required_fields_completeness",
        "protocol_validity_rate",
    }


def test_trajectory_and_trace_responses_have_no_private_provider_keys(tmp_path: Path) -> None:
    client = _client(tmp_path)

    trajectory = client.get(f"/api/runs/{L4}/cases/{CASE}/0/trajectory").json()
    trace = client.get(f"/api/runs/{L4}/cases/{CASE}/0/trace").json()
    encoded = json.dumps([trajectory, trace], sort_keys=True)

    assert FORBIDDEN.isdisjoint(set(_keys([trajectory, trace])))
    assert "reasoning_details" not in encoded
    assert trajectory["messages"]
    assert trace["events"]


def test_l4_replication_comparison_is_controlled_but_not_claimed_causal(tmp_path: Path) -> None:
    comparison = _client(tmp_path).get(
        f"/api/compare?run_a={SEQUENTIAL}&run_b={BATCH}"
    ).json()

    assert comparison["semantic_category"] == "controlled_fresh_generation_comparison"
    assert comparison["causal_claim_supported"] is False
    assert comparison["causal_reference"] is None
    assert comparison["compatibility"]["same_suite_fingerprint"] is True
    assert comparison["compatibility"]["same_code_revision"] is True
    assert comparison["compatibility"]["same_output_contract"] is True
    assert comparison["compatibility"]["same_treatment"] is False
    assert comparison["formal_metrics"]["execution_coverage"] == {
        "label": "Execution Coverage",
        "a": 1.0,
        "b": 1.0,
        "delta_pp": 0.0,
    }
    expected_deltas = {
        "failure_type_exact_match": 3.33333333333333,
        "report_evidence_hit_rate": -1.13624338624339,
        "required_fields_completeness": 4.79166666666667,
        "protocol_validity_rate": -1.66666666666667,
    }
    for metric, expected in expected_deltas.items():
        assert comparison["formal_metrics"][metric]["delta_pp"] == pytest.approx(
            expected
        )
    runtime = comparison["runtime_optimization"]
    assert runtime["interpretation"] == (
        "efficiency_reproduced_no_reproducible_material_quality_regression_demonstrated"
    )
    assert runtime["metrics"] == {
        "model_decisions": {"a": 877, "b": 571},
        "executed_tool_calls": {"a": 809, "b": 775},
        "input_tokens": {"a": 23448236, "b": 15696354},
        "output_tokens": {"a": 301898, "b": 286089},
        "total_tokens": {"a": 23750134, "b": 15982443},
        "run_wall_time_seconds": {"a": 978.270385, "b": 806.685981},
        "mean_sample_latency_seconds": {"a": 77.91716755, "b": 57.193100783333335},
        "p50_sample_latency_seconds": {"a": 63.134314, "b": 45.8250175},
        "p95_sample_latency_seconds": {"a": 184.51134615, "b": 132.7258861},
    }


def test_historical_fresh_comparison_is_not_labeled_causal(tmp_path: Path) -> None:
    comparison = _client(tmp_path).get(
        "/api/compare?run_a=dd8ca829-5051-43b6-a0c2-b3c2889acae0"
        f"&run_b={L4}"
    ).json()

    assert comparison["semantic_category"] == "historical_comparison"
    assert comparison["causal_claim_supported"] is False
    assert comparison["causal_reference"] is None
    assert comparison["runtime_optimization"] is None


def test_explicit_showcase_catalog_path_must_exist(monkeypatch, tmp_path: Path) -> None:
    missing = tmp_path / "missing-catalog.json"
    monkeypatch.setenv("DEVAGENTOPS_SHOWCASE_CATALOG_PATH", str(missing))

    with pytest.raises(RuntimeError, match="DEVAGENTOPS_SHOWCASE_CATALOG_PATH"):
        configured_showcase_catalog_path()


def test_explicit_showcase_catalog_path_is_used(monkeypatch, tmp_path: Path) -> None:
    catalog = tmp_path / "catalog.json"
    catalog.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("DEVAGENTOPS_SHOWCASE_CATALOG_PATH", str(catalog))

    assert configured_showcase_catalog_path() == catalog


def test_explorer_routes_are_get_only(tmp_path: Path) -> None:
    app = create_app(tmp_path / "local.db", explorer_catalog_path=CATALOG)
    explorer_methods = {
        method
        for route in app.routes
        if getattr(route, "path", "").startswith("/api")
        for method in getattr(route, "methods", set())
    }

    assert explorer_methods <= {"GET"}
