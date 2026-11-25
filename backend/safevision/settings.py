import importlib.util
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-safevision-smart-construction-safety-compliance-key'
)

DEBUG = os.environ.get(
    'DEBUG',
    'False' if os.environ.get('RENDER') else 'True'
).lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get('ALLOWED_HOSTS', '*').split(',') if h.strip()
]
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME and '*' not in ALLOWED_HOSTS and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://*.onrender.com,https://*.vercel.app').split(',')
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
# 1. DATABASE_URL (Render PostgreSQL / managed DB)
# 2. Local/external MySQL via MYSQL_* env vars
# 3. Seamless fallback to SQLite
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
    print("[SafeVision DB] Configured database from DATABASE_URL.")
else:
    MYSQL_NAME = os.environ.get('MYSQL_DATABASE', 'safevision')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'pavan')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')

    try:
        if os.environ.get('RENDER'):
            raise RuntimeError("Skipping local MySQL probe on Render without DATABASE_URL")
        import pymysql
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=int(MYSQL_PORT),
            connect_timeout=2
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
                'OPTIONS': {
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                    'charset': 'utf8mb4',
                }
            }
        }
        print("[SafeVision DB] Connected successfully to MySQL Database!")
    except Exception as e:
        print(f"[SafeVision DB] MySQL connection not active ({e}). Falling back seamlessly to SQLite.")
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.environ.get('SQLITE_PATH', str(BASE_DIR / 'db.sqlite3')),
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

_cors_origins = [
    o.strip() for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if o.strip()
]
if _cors_origins:
    CORS_ALLOWED_ORIGINS = _cors_origins
    CORS_ALLOW_ALL_ORIGINS = False
else:
    CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
