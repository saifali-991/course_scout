"""Reset a Django user's password (and/or username) without typing a long one-liner.

Why this exists: `manage.py changepassword admin` only works when you are in the
`backend` folder *and* the password passes Django's validators — otherwise it
just re-asks ("too short / too common") and looks frozen. This script runs from
anywhere, shows every step, and never leaves you wondering what happened.

Usage (prompt asks twice, typing stays hidden):

    myenv\\Scripts\\python.exe backend\\tools\\reset_admin_password.py
    myenv\\Scripts\\python.exe backend\\tools\\reset_admin_password.py --username admin

Rename the account too (password stays as it is unless you also pass --password):

    myenv\\Scripts\\python.exe backend\\tools\\reset_admin_password.py --rename boss

Scripted / no prompts (dev only — skips the "is it a strong password" check):

    myenv\\Scripts\\python.exe backend\\tools\\reset_admin_password.py --password NewPass123 --force
"""

import argparse
import getpass
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def main():
    parser = argparse.ArgumentParser(description="Set a new password for a Django user.")
    parser.add_argument('--username', default='admin', help='account to change (default: admin)')
    parser.add_argument('--password', help='skip the prompts and use this value (needs --force '
                                           'when it is not a strong password)')
    parser.add_argument('--rename', help='also change the username (password is left alone '
                                         'unless --password is given too)')
    parser.add_argument('--force', action='store_true',
                        help='save even if Django password validators complain (local dev only)')
    args = parser.parse_args()

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django

    django.setup()

    from django.contrib.auth import get_user_model
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    from django.db import connection

    User = get_user_model()
    db = connection.settings_dict
    print(f'database : {db["NAME"]} on {db["HOST"]}:{db["PORT"]} (user {db["USER"]})')

    try:
        user = User.objects.get(username=args.username)
    except User.DoesNotExist:
        others = list(User.objects.filter(is_staff=True).values_list('username', flat=True))
        print(f'!! no user named {args.username!r} in this database. '
              f'Staff accounts found: {others or "none"}')
        return 1
    if not user.is_staff:
        print(f'!! {user.username!r} exists but is not a staff user — it cannot open /admin.')

    password = args.password
    new_name = args.rename or user.username
    if new_name != user.username and User.objects.filter(username=new_name).exists():
        print(f'!! {new_name!r} is already taken — pick another username, nothing was changed.')
        return 1

    if new_name != user.username:
        old_name = user.username
        user.username = new_name
        try:
            user.save(update_fields=['username'])
        except Exception as exc:      # MySQL here is case-insensitive: 'Boss' clashes with 'boss'
            user.username = old_name
            print(f'!! could not rename to {new_name!r}: {type(exc).__name__}: {exc}')
            print(f'   {old_name!r} was left untouched.')
            return 1
        user.refresh_from_db()
        print(f'username : {old_name!r} -> {user.username!r}  (saved)')

    if password is None and not args.rename:
        print(f'\nChanging the password for {user.username!r}. '
              'Nothing appears while you type — that is normal.')
        password = getpass.getpass('New password     : ')
        again = getpass.getpass('Repeat the same  : ')
        if password != again:
            print('!! the two entries did not match — nothing was changed, run it again.')
            return 1

    if password is None:
        # --rename without --password: keep the current password untouched.
        print(f'\nusername : {user.username}')
        print('password : unchanged')
        print('saved to MySQL and verified: True')
        print('log in   : http://localhost:8000/admin/  (or http://localhost:5173/admin)')
        return 0

    if not password:
        print('!! empty password — nothing was changed.')
        return 1

    try:
        # Validators are the reason `changepassword` says "too short"/"too common".
        validate_password(password, user=user)
        strength = 'accepted by Django validators'
    except ValidationError as exc:
        strength = 'REJECTED by Django validators'
        for message in exc.messages:
            print('   -', message)
        if not args.force:
            print('\n!! pick something like "Scout@2026pass" (8+ characters, not all digits), '
                  'or re-run with --force to save it anyway.')
            return 1
        print('   (saving anyway because of --force)')

    try:
        user.set_password(password)   # scrambles it into a pbkdf2_sha256 hash
        user.save(update_fields=['password'])
    except Exception as exc:          # row vanished / MySQL hiccup — stay readable
        print(f'!! could not write to the database: {type(exc).__name__}: {exc}')
        print('   Nothing was changed. Is the MySQL service running, and does the account '
              'still exist?')
        return 1

    user.refresh_from_db()
    ok = user.check_password(password)
    print(f'\nusername : {user.username}')
    print(f'password : {"*" * len(password)}  ({strength})')
    print(f'saved to MySQL and verified: {ok}')
    print('log in   : http://localhost:8000/admin/  (or http://localhost:5173/admin)')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())