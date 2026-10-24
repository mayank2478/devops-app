"""Database setup with SQLAlchemy (PostgreSQL in Docker/RDS, SQLite in tests)."""
from datetime import datetime, timezone

from flask import Flask, current_app
from sqlalchemy import Boolean, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "done": self.done,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def init_db(app: Flask) -> None:
    engine = create_engine(app.config["DATABASE_URL"], pool_pre_ping=True)
    app.extensions["db_engine"] = engine
    app.extensions["db_session"] = sessionmaker(bind=engine, expire_on_commit=False)
    app.extensions["db_schema_ready"] = False
    # Try to create the tables now, but don't crash if the database isn't up
    # yet (common in Docker Compose / Kubernetes). /ready reports it, and the
    # tables are created on the first request once the database is reachable.
    try:
        ensure_schema(app)
    except Exception as exc:  # noqa: BLE001
        app.logger.warning("Database not reachable at startup: %s", exc)


def ensure_schema(app: Flask) -> None:
    # Simple for a demo. In a real project, use Alembic migrations instead.
    if not app.extensions["db_schema_ready"]:
        Base.metadata.create_all(app.extensions["db_engine"])
        app.extensions["db_schema_ready"] = True


def get_session():
    ensure_schema(current_app)
    return current_app.extensions["db_session"]()


def get_engine():
    return current_app.extensions["db_engine"]
