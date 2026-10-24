# 1. Base image: Python 3.12 on a small Debian ("slim") — README needs 3.10+
FROM python:3.12-slim

# 2. Python settings for containers:
#    - don't write .pyc files (useless in an image)
#    - print logs immediately, so `docker logs` / CloudWatch see them at once
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. All following commands run inside /app
WORKDIR /app

# 4. Create a non-root user to run the app (security best practice)
RUN useradd --create-home --uid 10001 appuser

# 5. Copy ONLY the dependency list first, then install.
#    Docker caches this layer, so changing your code later
#    does not reinstall every package.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the application code (.dockerignore keeps junk out).
#    --chown gives appuser ownership, so the app can write its local
#    SQLite file when no DATABASE_URL is set.
COPY --chown=appuser:appuser . .

# 7. From here on, run as the non-root user
USER appuser

# 8. Document the port the app listens on
EXPOSE 8000

# 9. Let Docker check the app is alive (slim has no curl, so use Python)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

# 10. Start with gunicorn (production server), not `python wsgi.py`
#     0.0.0.0  -> accept connections from outside the container
#     2 workers -> handle 2 requests at the same time
#     wsgi:app -> file wsgi.py, variable `app`
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "wsgi:app"]

