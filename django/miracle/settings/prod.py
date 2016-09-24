# Production Django settings
from .base import *
import os
import ConfigParser

# security settings
DEBUG = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

os.environ.setdefault('DB_USER', 'miracle')
os.environ.setdefault('DB_HOST', 'db')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB_NAME', 'miracle_metadata')
os.environ.setdefault('DATASETS_DB', 'miracle_datasets')
os.environ.setdefault('DEPLOYR_USER', 'miracle')
os.environ.setdefault('DEPLOYR_URL', 'http://deployr:8000')
os.environ.setdefault('RADIANT_URL', '/radiant/')

# DeployR settings
config = ConfigParser.RawConfigParser({'user': get_env_variable('DEPLOYR_USER')})
config.read('/code/deploy/deployr/deployr.conf')
DEFAULT_DEPLOYR_USER = config.get('deployr', 'user')
DEFAULT_DEPLOYR_PASSWORD = config.get('deployr', 'password')
DEPLOYR_URL = get_env_variable('DEPLOYR_URL')


# Radiant settings
# The url to link to the radiant frame with
# In production this is the link that you need to connect Radiant going through Nginx
# The https:// in the url should not be included
RADIANT_URL = get_env_variable('RADIANT_URL')

ALLOWED_HOSTS = ['.comses.net']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': 'FIXME: remember to edit this',
    },
    'datasets': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DATASETS_DB'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': 'FIXME: remember to edit this also',
    },
}
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

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
