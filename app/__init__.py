"""Application factory for the DevOps demo app."""
import os

from flask import Flask

from .db import init_db
from .routes import bp


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)

    # Settings come from environment variables, so the same image runs
    # locally (Docker Compose), in CI and on EKS without changes.
    app.config.update(
        DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///local.db"),
        APP_VERSION=os.getenv("APP_VERSION", "dev"),
        APP_ENV=os.getenv("APP_ENV", "local"),
    )
    if config:
        app.config.update(config)

    init_db(app)
    app.register_blueprint(bp)
    return app
