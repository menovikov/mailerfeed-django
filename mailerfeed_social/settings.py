import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '0m$k#e7930l)3n7hk$zu4^07f00txl)gl2@%dpdu#lcd53e3=-'

DEBUG = True

ALLOWED_HOSTS = ['*']


INSTALLED_APPS = [
    # 'django.contrib.admin',
    'user_registration',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    # 'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    # 'crispy_forms',
    'common',
    'vkconnector',
    'tgconnector',
    'notifications',
    'linker',
    'triggers',    
]


MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'mailerfeed_social.urls'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), "static_cdn")
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), "media_cdn")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.web_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'mailerfeed_social.wsgi.application'


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = (
    'common.authentication_backends.EmailAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
    )

LANGUAGE_CODE = 'ru-ru' 

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGIN_URL = '/auth/login/'

NOTIFICATIONS_DURING = {
    'hours': 24
}

# VK Specific configs
VK_CONF = {
    'APP_ID': 00000,
    'SECRET': 'qwertyqwerty',
    'SERVICE': 'qwertyqwerty',
}

# Telegram specific configs
TG_CONF = {
    'API_ID': 0000,
    'API_HASH': 'abcdabcd'
}
TG_DIR = os.path.join(BASE_DIR, "tgconnector", "tgcredentials")
if not os.path.exists(TG_DIR):
    os.mkdir(TG_DIR)

CRISPY_TEMPLATE_PACK = 'bootstrap3'

# Geolocation service
GEO_LINK = 'http://ip-api.com/json/'

DOMAIN = 'http://127.0.0.1:8000'

CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_IMPORTS = (
    'triggers.tasks',
)

# try:
#     from .settings_dev import *
# except ImportError:
#     pass
# try:
#     from .settings_prod import *
# except ImportError:
#     pass

LOGGING_PATH = os.path.join(os.path.dirname(BASE_DIR), "log/error_log.log")
if DEBUG:
    LOGGING_PATH = os.path.join(BASE_DIR, "error_log.log")


if not DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '[%(asctime)s] %(levelname)s %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'verbose': {
                'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
        },
        'handlers': {
            'log': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': LOGGING_PATH,
                'formatter' : 'simple',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['log'],
                'level': 'ERROR',
                'propagate': True,
            },
        },
    }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mailerdb',
        'USER': 'user',
        'PASSWORD': 'pass',
        'HOST': 'localhost',
        'PORT': '',
    },
}
