# CourseScout API — Django 5.2 behind gunicorn on port 8000.
#
#   docker build -t coursescout-api ./backend
#   docker run -p 8000:8000 --env-file backend/.env coursescout-api
#
# (Usually you go through `docker compose up` at the repo root instead.)

FROM python:3.11-slim

# PYTHONDONTWRITEBYTECODE: no .pyc noise in the image
# PYTHONUNBUFFERED:       print()/logs show up immediately in `docker logs`
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# mysqlclient needs a compiler + the MySQL client headers. They live in this
# layer only — the finished image still carries them (see .dockerignore), but
# keeping the install here means Python packages rebuild on their own cache.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first so this layer is cached across code changes.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the project (staticfiles/ and .env are excluded by .dockerignore).
COPY . .

# Collect admin/DRF assets into STATIC_ROOT for WhiteNoise. Needs no database,
# so it is safe to do at build time — the container starts with files ready.
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Run migrations (+ first-run seed) via the entrypoint, then hand over to gunicorn.
ENTRYPOINT ["sh", "docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-"]
