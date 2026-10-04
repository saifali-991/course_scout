"""Read-only helper: show which staff accounts exist and which password matches.

Usage:
    myenv\\Scripts\\python.exe backend\\tools\\check_admin_login.py

It never changes anything in the database — it only runs `check_password()`
against a list of likely candidates and prints the result.
"""

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()

staff = list(User.objects.filter(is_staff=True).values('username', 'is_superuser', 'is_active'))
print('staff accounts:', staff or 'NONE')

candidates = [
    'course1234', 'boss', 'admin', 'Boss@1234', 'Scout@2026pass',
    'password', 'boss@123', 'Boss1234', 'course12345', 'admin123',
    'Boss@2026', 'coursescout', 'Course1234',
]

for user in User.objects.filter(is_staff=True):
    hits = [c for c in candidates if user.check_password(c)]
    print(f'{user.username!r}: superuser={user.is_superuser} active={user.is_active} '
          f'hash={user.password.split("$")[0] if "$" in user.password else user.password[:20]} '
          f'matching candidates={hits or "none of the tested ones"}')
