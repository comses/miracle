"""
Django settings for miracle project.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

from __future__ import print_function

# Build projectpaths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys

from django.core.exceptions import ImproperlyConfigured

# tweaking standard BASE_DIR because we're in the settings subdirectory.
BASE_DIR = os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

DJANGO_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
)

THIRD_PARTY_APPS = (
    'django_extensions',
    'bootstrap3',
    'social.apps.django_app.default',
    'raven.contrib.django.raven_compat',
    'django_comments',
)

MIRACLE_APPS = (
    'miracle.core',
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + MIRACLE_APPS

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

# authentication backends for python social auth
# http://python-social-auth.readthedocs.org/en/latest/configuration/django.html
# http://www.artandlogic.com/blog/2014/04/tutorial-adding-facebooktwittergoogle-authentication-to-a-django-application/
# https://docs.djangoproject.com/en/1.9/topics/auth/customizing/#authentication-backends

AUTHENTICATION_BACKENDS = (
    'social.backends.github.GithubOAuth2',
    'social.backends.facebook.FacebookOAuth2',
    'social.backends.google.GoogleOAuth2',
    'social.backends.twitter.TwitterOAuth',
    'django.contrib.auth.backends.ModelBackend',
)

ROOT_URLCONF = 'miracle.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                # python-social-auth context processors
                'social.apps.django_app.context_processors.backends',
                'social.apps.django_app.context_processors.login_redirect',
                # expose SCM revision management to templates: https://github.com/klen/dealer
                'dealer.contrib.django.context_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'miracle.wsgi.application'

# Safely get environment variable function
def get_env_variable(var_name):
    """Get the environment variable or return exception"""
    val = os.environ.get(var_name)
    if val is None:
        raise ImproperlyConfigured("Set the {0} environment variable".format(var_name))
    return val


# Database configuration for metadata and ingested data
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'miracle_metadata',
        'USER': 'miracle',
        'PASSWORD': '',
    },
    'datasets': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'miracle_data',
        'USER': 'miracle',
        'PASSWORD': '',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = False

USE_L10N = False


# Logging
# https://docs.djangoproject.com/en/dev/topics/logging/


def is_accessible(directory_path):
    return os.path.isdir(directory_path) and os.access(directory_path, os.W_OK | os.X_OK)


def safe_make_paths(directory, fallback_directory, makedirs_callback):
    if not is_accessible(directory):
        try:
            makedirs_callback(directory)
        except OSError:
            print(
                "Cannot create absolute directory [%s]. Using relative path [%s] instead" %
                (directory, fallback_directory),
                file=sys.stderr)
            directory = fallback_directory
            if not is_accessible(directory):
                try:
                    makedirs_callback(directory)
                except OSError:
                    print("Couldn't create any [%s] directory, startup will fail" % directory,
                          file=sys.stderr)
    return directory


LOG_DIRECTORY = safe_make_paths('/miracle/logs', os.path.abspath('logs'), os.makedirs)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'INFO',
        'handlers': ['sentry', 'miracle.file', 'console'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s [%(name)s|%(funcName)s:%(lineno)d] %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'formatter': 'verbose',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'miracle.file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(LOG_DIRECTORY, 'miracle.log'),
            'backupCount': 6,
            'maxBytes': 10000000,
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'miracle': {
            'level': 'DEBUG',
            'handlers': ['miracle.file', 'console'],
            'propagate': False,
        },
    }
}

USE_TZ = True

LOGIN_URL = "/account/login/"
LOGIN_REDIRECT_URL = '/dashboard/'

# Django REST Framework configuration, see http://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.TemplateHTMLRenderer',
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
}

# Media files, see https://docs.djangoproject.com/en/1.9/ref/settings/#std:setting-MEDIA_ROOT for more details
# This absolute path specifies where all uploaded datasets will be sent. Can be overridden in local.py
# data directory to be exposed to DeployR / Radiant containers

MEDIA_URL = '/data/'

# Celery settings: http://celery.readthedocs.org

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis'
CELERY_ACCEPT_CONTENT = ['json', 'pickle']

def make_project_paths(project_directory):
    os.makedirs(project_directory)

def make_archive_path(archive_directory):
    os.makedirs('archives')

MIRACLE_PROJECT_DIRECTORY = safe_make_paths('/miracle/projects',
                                            os.path.abspath('projects'), make_project_paths)
MIRACLE_ARCHIVE_DIRECTORY = MEDIA_ROOT = safe_make_paths('/miracle/archives',
                                                         os.path.abspath('archives'), make_archive_path)
MIRACLE_PACKRAT_DIRECTORY = safe_make_paths('/miracle/packrat',
                                            os.path.abspath('packrat'), make_project_paths)
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = "/miracle/static/"

SITE_ID = 1

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'miracle', 'static'),
)
