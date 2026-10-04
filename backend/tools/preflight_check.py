"""Quick pre-flight check: DRF import + MySQL connectivity (uses backend/.env)."""

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def load_env():
    env = {}
    path = BACKEND / '.env'
    if not path.exists():
        print('!! .env not found at', path)
        return env
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, val = line.split('=', 1)
        env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def main():
    env = load_env()
    print('env keys:', sorted(env.keys()))

    try:
        import rest_framework  # noqa: F401
        print('DRF import: OK')
    except Exception as exc:  # pragma: no cover
        print('DRF import FAILED:', exc)

    try:
        import MySQLdb
        print('MySQLdb import: OK')
    except Exception as exc:  # pragma: no cover
        print('MySQLdb import FAILED:', exc)
        return

    try:
        conn = MySQLdb.connect(
            host=env.get('DB_HOST', 'localhost'),
            port=int(env.get('DB_PORT', 3306)),
            user=env.get('DB_USER', 'root'),
            passwd=env.get('DB_PASSWORD', ''),
        )
        cur = conn.cursor()
        cur.execute('SELECT VERSION()')
        print('MySQL server:', cur.fetchone()[0])
        name = env.get('DB_NAME', 'learning_platform')
        cur.execute('SHOW DATABASES LIKE %s', (name,))
        print(f'database {name!r} exists:', bool(cur.fetchall()))
        cur.close()
        conn.close()
    except Exception as exc:  # pragma: no cover
        print('MySQL connection FAILED:', exc)


if __name__ == '__main__':
    main()
