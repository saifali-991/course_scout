"""Read-only helper: show which staff accounts exist, and optionally test
passwords *you* type in.

Usage:

    myenv\\Scripts\\python.exe backend\\tools\\check_admin_login.py
    myenv\\Scripts\\python.exe backend\\tools\\check_admin_login.py --try 'SomePass1' --try 'Another1'

It only runs `check_password()` against what you pass on the command line and
prints the result — nothing is written to the database.

Security note: no password is stored in this file or anywhere else in the
repository on purpose (the repo is public). Guesses come from `--try` only, so a
real password can never end up in git history.
"""

import argparse
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description='List staff accounts / test candidate passwords (read-only).')
    parser.add_argument('--try', dest='candidates', action='append', default=[], metavar='PASSWORD',
                        help='candidate password to test against every staff account (repeatable)')
    parser.add_argument('--username', help='only inspect this account')
    args = parser.parse_args()

    User = get_user_model()
    staff = list(User.objects.filter(is_staff=True).values('username', 'is_superuser', 'is_active'))
    print('staff accounts:', staff or 'NONE')

    if args.username and not User.objects.filter(username=args.username, is_staff=True).exists():
        print(f'!! no staff user named {args.username!r}')
        return 1

    if not args.candidates:
        print('no candidates given — add --try <password> to test one (it is never stored anywhere)')
        return 0

    exit_code = 0
    for user in User.objects.filter(is_staff=True):
        if args.username and user.username != args.username:
            continue
        algo = user.password.split('$')[0] if '$' in user.password else user.password[:20]
        print(f'{user.username!r}: superuser={user.is_superuser} active={user.is_active} hash={algo}')
        hits = [c for c in args.candidates if user.check_password(c)]
        if hits:
            print(f'   MATCH — {len(hits)} of the candidates you passed work for this account')
        else:
            print('   none of the candidates you passed match')
            exit_code = 1
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())

