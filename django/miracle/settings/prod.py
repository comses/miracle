# Production Django settings
from .base import *
import os

# security settings
DEBUG = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

os.environ.setdefault('DB_USER', 'miracle')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DEPLOYR_USER', 'miracle')
os.environ.setdefault('DEPLOYR_URL', 'https://deployr.comses.net')
os.environ.setdefault('DEPLOYR_HOST', 'deployr.comses.net')
os.environ.setdefault('RADIANT_URL', 'https://miracle.comses.net/radiant/')

# DeployR settings
DEFAULT_DEPLOYR_USER = get_env_variable('DEPLOYR_USER')
DEFAULT_DEPLOYR_PASSWORD = 'changeme_deployr'
DEPLOYR_URL = get_env_variable('DEPLOYR_URL')
DEPLOYR_HOST = get_env_variable('DEPLOYR_HOST')


# Radiant settings
# The url to link to the radiant frame with
# In production this is the link that you need to connect Radiant going through Nginx
# The https:// in the url should not be included
RADIANT_URL = get_env_variable('RADIANT_URL')

ALLOWED_HOSTS = ['.comses.net']

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
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# disabling i18n until we need it
USE_I18N = False

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'CUSTOMIZE THIS'

SOCIAL_AUTH_FACEBOOK_KEY = 'customize this local secret key'
SOCIAL_AUTH_FACEBOOK_SECRET = 'customize this local secret key'

SOCIAL_AUTH_TWITTER_KEY = 'customize this local secret key'
SOCIAL_AUTH_TWITTER_SECRET = 'customize this local secret key'

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

SOCIAL_AUTH_GITHUB_KEY = ''
SOCIAL_AUTH_GITHUB_SECRET = ''

if not os.path.exists(MEDIA_ROOT):
    print("MEDIA_ROOT path '{}' does not exist, trying to create it now.".format(MEDIA_ROOT))
    try:
        os.makedirs(MEDIA_ROOT)
    except:
        print("Unable to create path {}, user uploads will not work properly.".format(MEDIA_ROOT))

RAVEN_CONFIG = {
    'dsn': '',
}
