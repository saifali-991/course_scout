"""Dump the resources_resource schema + row counts (MySQL Workbench equivalent)."""

import os
from pathlib import Path

import MySQLdb

BACKEND = Path(__file__).resolve().parents[1]


def load_env():
    env = {}
    for line in (BACKEND / '.env').read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def main():
    env = load_env()
    conn = MySQLdb.connect(
        host=env.get('DB_HOST', 'localhost'),
        port=int(env.get('DB_PORT', 3306)),
        user=env.get('DB_USER', 'root'),
        passwd=env.get('DB_PASSWORD', ''),
        db=env.get('DB_NAME', 'learning_platform'),
    )
    cur = conn.cursor()

    cur.execute('SHOW TABLES')
    print('tables:', [r[0] for r in cur.fetchall()])

    cur.execute('SHOW CREATE TABLE resources_resource')
    ddl = cur.fetchone()[1]
    for line in ddl.splitlines():
        if 'url' in line or 'KEY' in line or 'CREATE TABLE' in line:
            print(line)

    cur.execute('SELECT COUNT(*) FROM resources_resource')
    print('rows:', cur.fetchone()[0])

    print('columns:')
    cur.execute('SHOW COLUMNS FROM resources_resource')
    for col in cur.fetchall():
        print('  ', col[0], col[1], 'NULL' if col[2] == 'YES' else 'NOT NULL',
              f'key={col[3]}' if col[3] else '')

    cur.close()
    conn.close()


if __name__ == '__main__':
    main()
