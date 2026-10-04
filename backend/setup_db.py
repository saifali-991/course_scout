"""One-time helper: create the MySQL database from backend/.env credentials.

Run:  myenv\\Scripts\\python.exe backend\\setup_db.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

try:
    import MySQLdb as driver
except ImportError:
    import pymysql as driver  # type: ignore

DB_NAME = os.getenv('DB_NAME', 'learning_platform')
connect_kwargs = dict(
    host=os.getenv('DB_HOST', '127.0.0.1'),
    port=int(os.getenv('DB_PORT', '3306')),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    charset='utf8mb4',
)


def main():
    print(f"Connecting to MySQL {connect_kwargs['user']}@"
          f"{connect_kwargs['host']}:{connect_kwargs['port']} ...")
    try:
        conn = driver.connect(**connect_kwargs)
    except Exception as exc:  # noqa: BLE001 — surface a friendly message
        print(f'\n✗ Could not connect: {exc}')
        print('→ Check DB_USER / DB_PASSWORD in backend/.env, then re-run.')
        sys.exit(1)

    with conn.cursor() as cur:
        cur.execute(
            f'CREATE DATABASE IF NOT EXISTS `{DB_NAME}` '
            'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'
        )
    conn.commit()
    conn.close()
    print(f"✓ database '{DB_NAME}' is ready")


if __name__ == '__main__':
    main()
