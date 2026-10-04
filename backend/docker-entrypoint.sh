#!/bin/sh
# Runs before the real command (gunicorn) inside the backend container —
# shared by Docker Compose and Render, so both get the same startup steps:
#
#   1. apply migrations   (idempotent — safe on every boot)
#   2. seed the bundled starter courses, but ONLY while the DB is (nearly) empty
#   3. exec the command you passed (gunicorn …)
#
# Knobs (both optional):
#   SEED_ON_FIRST_RUN=0    never seed at all.
#   SEED_IF_ROWS_BELOW=N   seed only while the DB holds fewer than N resources.
#                          Default 1 → strictly an empty database.
#                          e.g. SEED_IF_ROWS_BELOW=1000 → seed unless 1000+ rows exist.
#
# Safety rule: when the row count cannot be read, seeding is SKIPPED. A remote
# DB (Clever Cloud, Render, …) that is briefly unreachable must never be
# mistaken for "0 rows".
set -e

echo "[entrypoint] applying migrations…"
python manage.py migrate --noinput

if [ "${SEED_ON_FIRST_RUN:-1}" = "1" ]; then
    # Capture stdout AND stderr: the old `2>/dev/null` hid a failed count query
    # and `${COUNT:-0}` then read "unknown" as "0 rows" → seed ran on a full DB.
    COUNT_RAW=$(python manage.py shell -c \
        "from resources.models import Resource; print(Resource.objects.count())" 2>&1) || true

    # Pure-digit lines only, so a stray warning can't be mistaken for the count.
    COUNT=$(printf '%s\n' "$COUNT_RAW" | grep -E '^[0-9]+$' | tail -n 1)

    # Threshold must be a plain number; anything else falls back to 1 (empty DB).
    SEED_BELOW=${SEED_IF_ROWS_BELOW:-1}
    case "$SEED_BELOW" in
        ''|*[!0-9]*) SEED_BELOW=1 ;;
    esac

    if [ -z "$COUNT" ]; then
        echo "[entrypoint] could not count resources — skipping seed (safe default)"
        printf '%s\n' "$COUNT_RAW" | tail -n 5 | sed 's/^/[entrypoint]   /'
    elif [ "$COUNT" -ge "$SEED_BELOW" ]; then
        echo "[entrypoint] database already has ${COUNT} resources (seed runs only below ${SEED_BELOW}) — skipping seed"
    else
        echo "[entrypoint] database has ${COUNT} resources (< ${SEED_BELOW}) → loading data/curated_courses_*.json (no API key needed)"
        python manage.py import_resources --only curated --skip-verify \
            || echo "[entrypoint] seeding failed — continuing anyway"
    fi
fi

exec "$@"
