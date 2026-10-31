"""SQLite storage: projects and their numbered versions (version history)."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    version INTEGER NOT NULL,
    text TEXT NOT NULL,
    requirements TEXT NOT NULL,
    stories TEXT NOT NULL,
    diagrams TEXT NOT NULL,
    changes TEXT NOT NULL,
    summary TEXT NOT NULL,
    created TEXT NOT NULL,
    UNIQUE(project_id, version)
);
"""


def _db_path() -> str:
    return os.environ.get("REQGENIE_DB", "data/reqgenie.db")


@contextmanager
def connect():
    path = _db_path()
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_project(name: str) -> int:
    with connect() as c:
        cur = c.execute("INSERT INTO projects (name, created) VALUES (?, ?)", (name, _now()))
        return cur.lastrowid


def add_version(project_id: int, text: str, result: dict) -> int:
    with connect() as c:
        row = c.execute("SELECT COALESCE(MAX(version), 0) AS v FROM versions WHERE project_id = ?",
                        (project_id,)).fetchone()
        version = row["v"] + 1
        c.execute(
            "INSERT INTO versions (project_id, version, text, requirements, stories, diagrams,"
            " changes, summary, created) VALUES (?,?,?,?,?,?,?,?,?)",
            (project_id, version, text, json.dumps(result["requirements"]),
             json.dumps(result["stories"]), json.dumps(result["diagrams"]),
             json.dumps(result["changes"]), json.dumps(result["summary"]), _now()),
        )
        return version


def list_projects() -> list[dict]:
    with connect() as c:
        rows = c.execute(
            "SELECT p.id, p.name, p.created, COALESCE(MAX(v.version), 0) AS latest_version "
            "FROM projects p LEFT JOIN versions v ON v.project_id = p.id "
            "GROUP BY p.id ORDER BY p.id DESC").fetchall()
        return [dict(r) for r in rows]


def get_project(project_id: int):
    with connect() as c:
        row = c.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return dict(row) if row else None


def list_versions(project_id: int) -> list[dict]:
    with connect() as c:
        rows = c.execute("SELECT version, created, summary FROM versions WHERE project_id = ? "
                         "ORDER BY version", (project_id,)).fetchall()
        return [{"version": r["version"], "created": r["created"],
                 "summary": json.loads(r["summary"])} for r in rows]


def get_version(project_id: int, version: int | None = None):
    with connect() as c:
        if version is None:
            row = c.execute("SELECT * FROM versions WHERE project_id = ? ORDER BY version DESC "
                            "LIMIT 1", (project_id,)).fetchone()
        else:
            row = c.execute("SELECT * FROM versions WHERE project_id = ? AND version = ?",
                            (project_id, version)).fetchone()
        if not row:
            return None
        return {
            "version": row["version"], "created": row["created"], "text": row["text"],
            "requirements": json.loads(row["requirements"]),
            "stories": json.loads(row["stories"]),
            "diagrams": json.loads(row["diagrams"]),
            "changes": json.loads(row["changes"]),
            "summary": json.loads(row["summary"]),
        }
