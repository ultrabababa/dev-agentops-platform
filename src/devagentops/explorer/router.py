from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from devagentops.explorer.schemas import TraceResponseDTO, TrajectoryResponseDTO
from devagentops.explorer.service import ExplorerService


def create_explorer_router(service: ExplorerService) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["evaluation-explorer"])

    def not_found(exc: KeyError) -> HTTPException:
        return HTTPException(status_code=404, detail=f"Explorer resource not found: {exc.args[0]}")

    @router.get("/overview")
    def overview():
        return service.overview()

    @router.get("/conditions")
    def conditions():
        return service.list_conditions()

    @router.get("/conditions/{condition}")
    def condition_detail(condition: str):
        try:
            return service.get_condition(condition)
        except KeyError as exc:
            raise not_found(exc) from exc

    @router.get("/experiments/evolution")
    def experiment_evolution():
        return service.experiment_evolution()

    @router.get("/runs")
    def runs():
        return service.repository.list_runs()

    @router.get("/runs/{run_id}")
    def run_detail(run_id: str):
        try:
            return service.repository.get_run(run_id)
        except KeyError as exc:
            raise not_found(exc) from exc

    @router.get("/runs/{run_id}/cases")
    def run_cases(run_id: str):
        try:
            service.repository.get_run(run_id)
            return service.repository.list_run_cases(run_id)
        except KeyError as exc:
            raise not_found(exc) from exc

    @router.get("/runs/{run_id}/cases/{case_id}/{repeat_index}")
    def sample_detail(run_id: str, case_id: str, repeat_index: int):
        try:
            return service.repository.get_sample(run_id, case_id, repeat_index)
        except KeyError as exc:
            raise not_found(exc) from exc

    @router.get(
        "/runs/{run_id}/cases/{case_id}/{repeat_index}/trajectory",
        response_model=TrajectoryResponseDTO,
    )
    def trajectory(run_id: str, case_id: str, repeat_index: int):
        try:
            return service.trajectory(run_id, case_id, repeat_index)
        except KeyError as exc:
            raise not_found(exc) from exc

    @router.get(
        "/runs/{run_id}/cases/{case_id}/{repeat_index}/trace",
        response_model=TraceResponseDTO,
    )
    def trace(run_id: str, case_id: str, repeat_index: int):
        try:
            return service.trace(run_id, case_id, repeat_index)
        except KeyError as exc:
            raise not_found(exc) from exc

    @router.get("/cases")
    def cases():
        return service.list_cases()

    @router.get("/cases/{case_id}")
    def case_detail(case_id: str):
        try:
            return service.get_case(case_id)
        except KeyError as exc:
            raise not_found(exc) from exc

    @router.get("/comparisons")
    def comparisons():
        return service.comparisons()

    @router.get("/compare")
    def compare(run_a: str = Query(...), run_b: str = Query(...)):
        try:
            return service.compare(run_a, run_b)
        except KeyError as exc:
            raise not_found(exc) from exc

    return router
