import os
import sys
import pytz
from datetime import datetime

from django.utils.translation import ugettext_lazy as _
from celery.schedules import crontab
from requests.packages.urllib3.util.retry import Retry

PRODUCTION_URL = os.environ.get('API_FQDN')
# Requires uppercase variable https://docs.djangoproject.com/en/2.1/topics/settings/#creating-your-own-settings

localhost = 'localhost'
BASE_URL = PRODUCTION_URL if PRODUCTION_URL else '%s:8000' % localhost

# Backend URL nicing:
if BASE_URL == 'prddsgocdnapi.azureedge.net':
    BASE_URL = 'goadmin.ifrc.org'
# The frontend_url nicing is in frontend.py

INTERNAL_IPS = ['127.0.0.1']
if 'DOCKER_HOST_IP' in os.environ:
    INTERNAL_IPS.append(os.environ['DOCKER_HOST_IP'])

DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': [
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
    ],
}

ALLOWED_HOSTS = [localhost, '0.0.0.0']
if PRODUCTION_URL is not None:
    ALLOWED_HOSTS.append(PRODUCTION_URL)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = False if PRODUCTION_URL is not None else True

# See if we are inside a test environment
TESTING = any([
    arg in sys.argv for arg in [
        'test',
        'pytest',
        'py.test',
        '/usr/local/bin/pytest',
        '/usr/local/bin/py.test',
        '/usr/local/lib/python3.6/dist-packages/py/test.py',
    ]
    # Provided by pytest-xdist (If pytest is used)
]) or os.environ.get('PYTEST_XDIST_WORKER') is not None


INSTALLED_APPS = [
    # External App (This app has to defined before django.contrib.admin)
    'modeltranslation',  # https://django-modeltranslation.readthedocs.io/en/latest/installation.html#installed-apps

    # Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_admin_listfilter_dropdown',
    'corsheaders',
    'tastypie',
    'rest_framework',
    'rest_framework.authtoken',
    'guardian',
    'django_filters',
    'graphene_django',

    # GO Apps
    'api',
    'per',
    'notifications',
    'registrations',
    'deployments',
    'databank',
    'lang',

    # Utils Apps
    'tinymce',
    'admin_auto_filters',
    'django_celery_beat',

    # Logging
    'reversion',
    'reversion_compare',

    # Debug
    'debug_toolbar',

    # GIS
    'django.contrib.gis'
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_csv.renderers.PaginatedCSVRenderer',
    ),
}

GRAPHENE = {
    'SCHEMA': 'api.schema.schema'
}

FILE_STORAGE = {
    'LOCATION': 'media',
}

AZURE_STORAGE = {
    'CONTAINER': 'api',
    'ACCOUNT_NAME': os.environ.get('AZURE_STORAGE_ACCOUNT'),
    'ACCOUNT_KEY': os.environ.get('AZURE_STORAGE_KEY'),
    'USE_SSL': False,
}

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middlewares.middlewares.RequestMiddleware',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'main.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'notifications/templates/'),
            os.path.join(BASE_DIR, 'api/templates/'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'main.context_processors.ifrc_go',
            ],
        },
    },
]

WSGI_APPLICATION = 'main.wsgi.application'

# Use local postgres for dev, env-determined for production
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('DJANGO_DB_NAME'),
        'USER': os.environ.get('DJANGO_DB_USER'),
        'PASSWORD': os.environ.get('DJANGO_DB_PASS'),
        'HOST': os.environ.get('DJANGO_DB_HOST'),
        'PORT': os.environ.get('DJANGO_DB_PORT'),
    }
}

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

TINYMCE_DEFAULT_CONFIG = {
    'entity_encoding': 'raw',
    'height': 360,
    'width': 1120,
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'selector': 'textarea',
    'theme': 'modern',
    'plugins': '''
            textcolor save link image media preview codesample contextmenu
            table code lists fullscreen  insertdatetime  nonbreaking
            contextmenu directionality searchreplace wordcount visualblocks
            visualchars code fullscreen autolink lists  charmap print  hr
            anchor pagebreak
            ''',
    'toolbar1': '''
            bold italic underline fontsizeselect
            | forecolor | alignleft alignright | aligncenter alignjustify
            | indent outdent | bullist numlist |
            | link visualchars charmap hr nonbreaking | code preview fullscreen
            ''',
    'toolbar2': '''
            media embed
            ''',
    'force_p_newlines': False,
    'forced_root_block': '',
    'contextmenu': 'formats | link',
    'menubar': True,
    'statusbar': True,
    # 'extended_valid_elements': 'iframe[src|frameborder|style|scrolling|class|width|height|name|align]',

    # If more formatting possibilities needed (or more rows), choose from these:
    # 'toolbar1': '''
    # fullscreen preview bold italic underline | fontselect,
    # fontsizeselect  | forecolor backcolor | alignleft alignright |
    # aligncenter alignjustify | indent outdent | bullist numlist table |
    # | link image media | codesample |
    # ''',
    # 'toolbar2': '''
    # visualblocks visualchars |
    # charmap hr pagebreak nonbreaking anchor |  code |
    # ''',
}

LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = (
    ('en', _('English')),
    ('es', _('Spanish')),
    ('fr', _('French')),
    ('ar', _('Arabic')),
)
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
MODELTRANSLATION_FALLBACK_LANGUAGES = ('en', 'fr', 'es', 'ar')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Email config
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASS')

DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # default 2621440, 2.5MB -> 100MB
# default 1000, was not enough for Mozambique Cyclone Idai data
# second  2000, was not enouch for Global COVID Emergency
DATA_UPLOAD_MAX_NUMBER_FIELDS = 3000
timezone = pytz.timezone("Europe/Zurich")
PER_LAST_DUEDATE = timezone.localize(datetime(2018, 11, 15, 9, 59, 25, 0))
PER_NEXT_DUEDATE = timezone.localize(datetime(2023, 11, 15, 9, 59, 25, 0))

FDRS_APIKEY = os.environ.get('FDRS_APIKEY')
FDRS_CREDENTIAL = os.environ.get('FDRS_CREDENTIAL')
HPC_CREDENTIAL = os.environ.get('HPC_CREDENTIAL')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'timestamp': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'api.filehandler.MakeFileHandler',
            'filename': '../logs/logger.log',
            'formatter': 'timestamp',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# AWS Translate Credentials
AWS_TRANSLATE_ACCESS_KEY = os.environ.get('AWS_TRANSLATE_ACCESS_KEY')
AWS_TRANSLATE_SECRET_KEY = os.environ.get('AWS_TRANSLATE_SECRET_KEY')
AWS_TRANSLATE_REGION = os.environ.get('AWS_TRANSLATE_REGION')

TEST_RUNNER = 'snapshottest.django.TestRunner'

# CELERY CONFIG
CELERY_REDIS_URL = os.environ.get('CELERY_REDIS_URL', 'redis://redis:6379/0')  # "redis://:{password}@{host}:{port}/{db}"
CELERY_BROKER_URL = CELERY_REDIS_URL
CELERY_RESULT_BACKEND = CELERY_REDIS_URL
CELERY_TIMEZONE = TIME_ZONE
CELERY_ACKS_LATE = True

# CELERY_BEAT_SCHEDULE = {
#     'translate_remaining_models_fields': {
#         'task': 'lang.tasks.translate_remaining_models_fields',
#         # Every 6 hour
#         'schedule': crontab(minute=0, hour="*/6"),
#     },
# }

RETRY_STRATEGY = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"]
)
