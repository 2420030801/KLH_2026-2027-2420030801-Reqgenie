"""ReqGenie API (FastAPI) + static web front end."""
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import engine, store
from .export import to_jira_csv, to_markdown

app = FastAPI(title="ReqGenie", version="1.0.0",
              description="Turns client requirements into user stories, acceptance criteria "
                          "and UML diagrams, and adapts when requirements change.")


class NewProject(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    text: str = Field(min_length=3, max_length=50_000)


class UpdateText(BaseModel):
    text: str = Field(min_length=3, max_length=50_000)


def _require_project(project_id: int) -> dict:
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


def _payload(project: dict, version: int, data: dict) -> dict:
    return {"project_id": project["id"], "name": project["name"], "version": version, **data}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/projects")
def create_project(body: NewProject):
    result = engine.generate(body.text)
    if not result["stories"]:
        raise HTTPException(422, "No requirements found. Write full sentences such as "
                                 "'Customers can search products'.")
    project_id = store.create_project(body.name.strip())
    version = store.add_version(project_id, body.text, result)
    return _payload(store.get_project(project_id), version, result)


@app.get("/api/projects")
def list_projects():
    return store.list_projects()


@app.post("/api/projects/{project_id}/update")
def update_project(project_id: int, body: UpdateText):
    project = _require_project(project_id)
    previous = store.get_version(project_id)
    if previous is None:
        raise HTTPException(409, "Project has no version to update")
    result = engine.update(previous["requirements"], previous["stories"], body.text)
    if not result["stories"]:
        raise HTTPException(422, "No requirements found in the updated text")
    version = store.add_version(project_id, body.text, result)
    return _payload(project, version, result)


@app.get("/api/projects/{project_id}/versions")
def versions(project_id: int):
    _require_project(project_id)
    return store.list_versions(project_id)


@app.get("/api/projects/{project_id}/versions/{version}")
def get_version(project_id: int, version: int):
    project = _require_project(project_id)
    data = store.get_version(project_id, version)
    if not data:
        raise HTTPException(404, "Version not found")
    return _payload(project, version, data)


@app.get("/api/projects/{project_id}/export")
def export(project_id: int, format: str = Query("md", pattern="^(md|csv)$"),
           version: int | None = None):
    project = _require_project(project_id)
    data = store.get_version(project_id, version)
    if not data:
        raise HTTPException(404, "Version not found")
    safe = "".join(ch if ch.isalnum() else "_" for ch in project["name"]) or "reqgenie"
    if format == "csv":
        return Response(to_jira_csv(data), media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{safe}.csv"'})
    return Response(to_markdown(project["name"], data["version"], data),
                    media_type="text/markdown",
                    headers={"Content-Disposition": f'attachment; filename="{safe}.md"'})


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
