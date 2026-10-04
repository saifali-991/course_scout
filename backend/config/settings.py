"""
CourseScout — Django settings (config/settings.py)

All secrets & database credentials load from `backend/.env` (never committed).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load backend/.env before anything reads os.getenv('DB_...')
load_dotenv(BASE_DIR / '.env')

# --- MySQL driver ------------------------------------------------------------
# Prefer mysqlclient; if it isn't installed (e.g. no MSVC build tools on
# Python 3.14) fall back to pure-python PyMySQL transparently.
try:
    import MySQLdb  # noqa: F401  — mysqlclient
except ImportError:  # pragma: no cover
    try:
        import pymysql

        pymysql.install_as_MySQLdb()
        pymysql.version_info = (1, 4, 6, 'final', 0)  # satisfy Django's check
    except ImportError:
        pass


SECRET_KEY = os.getenv('SECRET_KEY', 'dev-insecure-key-change-me')
DEBUG = os.getenv('DEBUG', 'True').strip().lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if h.strip()
]
if DEBUG and '*' not in ALLOWED_HOSTS:
    # Dev convenience: while DEBUG is on, also answer requests that arrive with a
    # LAN hostname/IP (192.168.x.x, your machine name, a phone on the same Wi-Fi).
    # Without this Django replies "400 Bad Request: Invalid HTTP_HOST header",
    # which looks exactly like "the admin page just won't open".
    # Ignored when DEBUG=False — production must set ALLOWED_HOSTS in .env.
    ALLOWED_HOSTS.append('*')

# --- Applications ------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # third-party
    'rest_framework',
    'corsheaders',
    'django_filters',
    # local
    'resources',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # must stay above CommonMiddleware
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serves the collected admin/DRF assets straight from gunicorn,
    # so production needs no separate web server for /static/. Must sit right
    # after SecurityMiddleware (its own requirement) and before everything that
    # might redirect to a missing CSS file.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- Database (MySQL — credentials from .env) --------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'learning_platform'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# --- Django REST Framework ---------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'resources.pagination.ResourcesPagination',
    'PAGE_SIZE': 8,
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# --- CORS (React dev server) -------------------------------------------------

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173',
    ).split(',')
    if o.strip()
]
# --- CSRF behind the Vite proxy -----------------------------------------------
# frontend/vite.config.js proxies /admin to Django with changeOrigin, so an admin
# login POST sent from http://localhost:5173 arrives as
#   Host: 127.0.0.1:8000  +  Origin: http://localhost:5173
# and Django's CSRF origin check rejects it with "403 CSRF Verification failed" —
# the login page just reloads and looks like a wrong password. Trusting the dev
# server origins makes http://localhost:5173/admin behave like :8000/admin.
CSRF_TRUSTED_ORIGINS = set(CORS_ALLOWED_ORIGINS)
if DEBUG:  # Vite moves to 5174 when 5173 is busy
    CSRF_TRUSTED_ORIGINS |= {
        f'http://{host}:{port}'
        for host in ('localhost', '127.0.0.1')
        for port in (5173, 5174)
    }
for _origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(','):
    if _origin.strip():
        CSRF_TRUSTED_ORIGINS.add(_origin.strip())
CSRF_TRUSTED_ORIGINS = sorted(CSRF_TRUSTED_ORIGINS)

# --- Defaults ----------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Kolkata')
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

# Where `collectstatic` drops the admin/DRF CSS+JS (WhiteNoise serves it in
# production). git-ignored locally, created inside the Docker image at build.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Optional TLS for a managed MySQL (Aiven / Clever Cloud / PlanetScale…):
#   DB_SSL=true        turn on TLS with the driver's defaults
#   DB_SSL_CA=/path/x  also pin the provider's CA certificate
# Left off by default — local MySQL doesn't use TLS.
if os.getenv('DB_SSL', '').strip().lower() in ('1', 'true', 'yes'):
    _ssl_opts = {}
    if os.getenv('DB_SSL_CA', '').strip():
        _ssl_opts['ca'] = os.getenv('DB_SSL_CA').strip()
    DATABASES['default']['OPTIONS']['ssl'] = _ssl_opts

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
