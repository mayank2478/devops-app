# DevOps Demo App — Task List API

A small Flask API used as the application for the AWS DevOps project
(Docker → Jenkins → ECR → Argo CD → EKS → RDS).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | App name, version, environment, hostname (pod name on EKS) |
| GET | `/health` | Liveness check — process is up |
| GET | `/ready` | Readiness check — database reachable (503 if not) |
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create a task: `{"title": "..."}` |
| PATCH | `/api/tasks/<id>` | Update: `{"done": true}` or `{"title": "..."}` |
| DELETE | `/api/tasks/<id>` | Delete a task |

## Project layout

```
devops-app/
├── app/
│   ├── __init__.py      # create_app() — reads settings from env vars
│   ├── db.py            # SQLAlchemy engine + Task table
│   └── routes.py        # all endpoints
├── tests/
│   └── test_app.py      # pytest tests (use SQLite, no Postgres needed)
├── wsgi.py              # entry point: `app` object for gunicorn
├── requirements.txt     # runtime dependencies
└── requirements-dev.txt # + pytest
```

## Run locally (WSL / Ubuntu)

```bash
cd devops-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# run the tests
pytest -v

# start the app (uses a local SQLite file by default)
python wsgi.py
```

Try it in another terminal:

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/tasks \
     -H "Content-Type: application/json" -d '{"title":"learn docker"}'
curl http://localhost:8000/api/tasks
```

## Configuration (environment variables)

| Variable | Default | Example |
|---|---|---|
| `DATABASE_URL` | `sqlite:///local.db` | `postgresql+psycopg://appuser:secret@db:5432/appdb` |
| `APP_VERSION` | `dev` | the git commit SHA, set by CI |
| `APP_ENV` | `local` | `dev`, `staging`, `prod` |

Note the PostgreSQL URL must start with `postgresql+psycopg://` (psycopg 3 driver).

## Notes for writing your Dockerfile

- **Base image:** Python 3.10 or newer (the code uses `dict | None` type hints). `python:3.12-slim` is a good choice.
- **Install:** `pip install -r requirements.txt` (not the dev file, keep pytest out of the image).
- **Port:** the app listens on **8000**.
- **Production server:** run with gunicorn, not `python wsgi.py`:
  `gunicorn --bind 0.0.0.0:8000 --workers 2 wsgi:app`
- **Health check:** `/health` returns 200 when the app is up.
- **Don't copy** `.venv/`, `__pycache__/`, `*.db` or `tests/` into the image — use a `.dockerignore`.
