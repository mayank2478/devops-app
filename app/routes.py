"""HTTP routes: info, health checks and a small tasks API."""
import socket

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select, text

from .db import Task, get_engine, get_session

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    # hostname = the container / pod name, handy later to see load balancing on EKS
    return jsonify(
        app="devops-demo",
        version=current_app.config["APP_VERSION"],
        environment=current_app.config["APP_ENV"],
        hostname=socket.gethostname(),
    )


@bp.get("/health")
def health():
    """Liveness probe: the process is up."""
    return jsonify(status="ok")


@bp.get("/ready")
def ready():
    """Readiness probe: the app can reach the database."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify(status="ready", database="ok")
    except Exception as exc:  # noqa: BLE001
        current_app.logger.warning("Readiness check failed: %s", exc)
        return jsonify(status="not ready", database="unreachable"), 503


@bp.get("/api/tasks")
def list_tasks():
    with get_session() as session:
        tasks = session.scalars(select(Task).order_by(Task.id)).all()
        return jsonify([t.to_dict() for t in tasks])


@bp.post("/api/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify(error="title is required"), 400
    if len(title) > 200:
        return jsonify(error="title must be 200 characters or fewer"), 400

    with get_session() as session:
        task = Task(title=title)
        session.add(task)
        session.commit()
        return jsonify(task.to_dict()), 201


@bp.patch("/api/tasks/<int:task_id>")
def update_task(task_id: int):
    data = request.get_json(silent=True) or {}
    with get_session() as session:
        task = session.get(Task, task_id)
        if task is None:
            return jsonify(error="task not found"), 404
        if "done" in data:
            task.done = bool(data["done"])
        if "title" in data:
            title = str(data["title"]).strip()
            if not title:
                return jsonify(error="title cannot be empty"), 400
            task.title = title
        session.commit()
        return jsonify(task.to_dict())


@bp.delete("/api/tasks/<int:task_id>")
def delete_task(task_id: int):
    with get_session() as session:
        task = session.get(Task, task_id)
        if task is None:
            return jsonify(error="task not found"), 404
        session.delete(task)
        session.commit()
        return "", 204
