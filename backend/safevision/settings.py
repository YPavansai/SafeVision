import importlib.util
import logging
import os
import re
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(env_path):
    """Lightweight .env loader so local dev works without extra dependencies."""
    if not env_path.exists():
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


_load_dotenv(BASE_DIR.parent / '.env')
_load_dotenv(BASE_DIR / '.env')

DJANGO_ENV = os.environ.get(
    'DJANGO_ENV',
    'production' if os.environ.get('RENDER') else 'development'
).lower()
IS_PRODUCTION = DJANGO_ENV == 'production'

DEBUG = os.environ.get(
    'DEBUG',
    'False' if IS_PRODUCTION else 'True'
).lower() in ('true', '1', 'yes')

_DEFAULT_DEV_SECRET = 'django-insecure-safevision-dev-only-key-change-in-production'
SECRET_KEY = os.environ.get('SECRET_KEY')
if IS_PRODUCTION and (not SECRET_KEY or SECRET_KEY == _DEFAULT_DEV_SECRET or SECRET_KEY.startswith('django-insecure-')):
    raise ImproperlyConfigured("A strong SECRET_KEY environment variable is required in production.")
if not SECRET_KEY:
    SECRET_KEY = _DEFAULT_DEV_SECRET

_default_hosts = 'localhost,127.0.0.1' if not IS_PRODUCTION else '.onrender.com'
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get('ALLOWED_HOSTS', _default_hosts).split(',') if h.strip()
]
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME and '*' not in ALLOWED_HOSTS and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

_default_frontend_origins = 'http://localhost:3000,http://127.0.0.1:3000,https://safe-vision-tan.vercel.app'
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        'CSRF_TRUSTED_ORIGINS',
        f'{_default_frontend_origins},https://*.onrender.com,https://*.vercel.app'
    ).split(',')
    if origin.strip()
]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',

    # Local apps
    'api.apps.ApiConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    *(
        ['whitenoise.middleware.WhiteNoiseMiddleware']
        if importlib.util.find_spec('whitenoise') is not None
        else []
    ),
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'api.middleware.RequestLoggingMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'safevision.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'safevision.wsgi.application'

# Database configuration:
# Production: requires DATABASE_URL or reachable MySQL (NO silent SQLite fallback).
# Development: tries MySQL (with connection pooling), falls back to SQLite for local dev/testing.
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=int(os.environ.get('DB_CONN_MAX_AGE', 600)),
            conn_health_checks=True,
            ssl_require=IS_PRODUCTION,
        )
    }
else:
    MYSQL_NAME = os.environ.get('MYSQL_DATABASE', 'safevision')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '' if IS_PRODUCTION else 'pavan')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')

    if IS_PRODUCTION:
        if not MYSQL_PASSWORD:
            raise ImproperlyConfigured(
                "Production database requires DATABASE_URL or MYSQL_PASSWORD environment variable."
            )
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': MYSQL_NAME,
                'USER': MYSQL_USER,
                'PASSWORD': MYSQL_PASSWORD,
                'HOST': MYSQL_HOST,
                'PORT': MYSQL_PORT,
                'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', 600)),
                'CONN_HEALTH_CHECKS': True,
                'OPTIONS': {
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                    'charset': 'utf8mb4',
                    'connect_timeout': 5,
                },
            }
        }
    else:
        try:
            import pymysql
            connection = pymysql.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                port=int(MYSQL_PORT),
                connect_timeout=2,
            )
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_NAME}` CHARACTER SET utf8mb4;")
            connection.close()

            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.mysql',
                    'NAME': MYSQL_NAME,
                    'USER': MYSQL_USER,
                    'PASSWORD': MYSQL_PASSWORD,
                    'HOST': MYSQL_HOST,
                    'PORT': MYSQL_PORT,
                    'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', 60)),
                    'CONN_HEALTH_CHECKS': True,
                    'OPTIONS': {
                        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                        'charset': 'utf8mb4',
                        'connect_timeout': 5,
                    },
                }
            }
            print("[SafeVision DB] Connected to MySQL Database.")
        except Exception:
            print("[SafeVision DB] Local MySQL unavailable; using development SQLite database.")
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': os.environ.get('SQLITE_PATH', str(BASE_DIR / 'db.sqlite3')),
                    'OPTIONS': {
                        'timeout': 20,
                    },
                }
            }

# Caching: Redis if REDIS_URL is set, otherwise fast in-process LocMemCache
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'TIMEOUT': 60,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'safevision-cache',
            'TIMEOUT': 60,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
if importlib.util.find_spec('whitenoise') is not None:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))

# Upload size caps (16 MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 16 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 16 * 1024 * 1024

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAdminUser',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.environ.get('THROTTLE_ANON', '60/min'),
        'user': os.environ.get('THROTTLE_USER', '300/min'),
        'login': os.environ.get('THROTTLE_LOGIN', '10/min'),
        'ai_inference': os.environ.get('THROTTLE_AI', '60/min'),
        'forgot_password': '5/min',
    },
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('JWT_ACCESS_MINUTES', 30))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.environ.get('JWT_REFRESH_DAYS', 7))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Configuration
_cors_origins = [
    o.strip()
    for o in os.environ.get('CORS_ALLOWED_ORIGINS', _default_frontend_origins).split(',')
    if o.strip()
]
CORS_ALLOWED_ORIGINS = _cors_origins
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https://.*\.vercel\.app$',
]
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'False').lower() in ('true', '1', 'yes')
CORS_ALLOW_CREDENTIALS = True

# HTTP Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

if IS_PRODUCTION and not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 'yes')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Optional Celery Config
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', '')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', '')
CELERY_TASK_TIME_LIMIT = 120
CELERY_TASK_SOFT_TIME_LIMIT = 90
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
USE_CELERY = os.environ.get('USE_CELERY', 'False').lower() in ('true', '1', 'yes')


class SensitiveDataFilter(logging.Filter):
    """Redacts JWT tokens, passwords, and connection strings from logs."""

    _PATTERNS = [
        (re.compile(r'(Bearer\s+)[A-Za-z0-9\-_\.]+', re.IGNORECASE), r'\1[REDACTED]'),
        (re.compile(r'("?(?:password|secret|token|refresh|access)"?\s*[:=]\s*)"?[^",\s}]+"?', re.IGNORECASE), r'\1[REDACTED]'),
        (re.compile(r'(postgres|mysql|redis)://[^@\s]+@', re.IGNORECASE), r'\1://[REDACTED]@'),
    ]

    def filter(self, record):
        msg = record.getMessage()
        for pat, repl in self._PATTERNS:
            msg = pat.sub(repl, msg)
        record.msg = msg
        record.args = ()
        return True


LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'redact_secrets': {
            '()': 'safevision.settings.SensitiveDataFilter',
        },
    },
    'formatters': {
        'structured': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'structured',
            'filters': ['redact_secrets'],
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'safevision.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'structured',
            'filters': ['redact_secrets'],
        },
    },
    'loggers': {
        'safevision': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'safevision.security': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'safevision.performance': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'safevision.ai': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
