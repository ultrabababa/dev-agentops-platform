"""Lesson 0005: expose process health and package version over HTTP."""

from fastapi import FastAPI

from devagentops import __version__


app = FastAPI(title="DevAgentOps", version=__version__)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": __version__}