"""Extract a wheel file directly into site-packages (bypasses a hanging pip).

Usage: python install_wheel.py <path-to-whl>
"""

import os
import shutil
import sys
import zipfile


def main():
    if len(sys.argv) != 2:
        print('usage: install_wheel.py <wheel-file>')
        sys.exit(1)
    whl = sys.argv[1]
    # target site-packages of THIS venv
    import sysconfig
    sp = sysconfig.get_paths()['purelib']
    print(f'target site-packages: {sp}')

    pkg_guess = None
    with zipfile.ZipFile(whl) as z:
        top = sorted({n.split('/')[0] for n in z.namelist()})
        print('wheel contains:', top)
        for name in top:
            if name.endswith('.dist-info'):
                pkg_guess = name
        # remove any previous (possibly partial) install of these packages
        for name in top:
            if name == 'django':
                shutil.rmtree(os.path.join(sp, name), ignore_errors=True)
            elif name.endswith('.dist-info'):
                shutil.rmtree(os.path.join(sp, name), ignore_errors=True)
        z.extractall(sp)

    print(f'✓ extracted {pkg_guess} into {sp}')


if __name__ == '__main__':
    main()
