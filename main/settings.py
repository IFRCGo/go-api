import os
from datetime import datetime
import pytz

PRODUCTION_URL = os.environ.get('API_FQDN')
# Requires uppercase variable https://docs.djangoproject.com/en/2.1/topics/settings/#creating-your-own-settings

localhost = 'localhost'
BASE_URL = PRODUCTION_URL if PRODUCTION_URL else '%s:8000' % localhost

# Backend URL nicing:
if BASE_URL == 'prddsgocdnapi.azureedge.net':
    BASE_URL = 'goadmin.ifrc.org'
# The frontend_url nicing is in frontend.py

ALLOWED_HOSTS = [localhost, '0.0.0.0']
if PRODUCTION_URL is not None:
    ALLOWED_HOSTS.append(PRODUCTION_URL)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = False if PRODUCTION_URL is not None else True

INSTALLED_APPS = [
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

    # Utils Apps
    'tinymce',

    # Logging
    'reversion',
    'reversion_compare',
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

AZURE_STORAGE = {
    'CONTAINER': 'api',
    'ACCOUNT_NAME': os.environ.get('AZURE_STORAGE_ACCOUNT'),
    'ACCOUNT_KEY': os.environ.get('AZURE_STORAGE_KEY'),
    'USE_SSL': False,
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
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
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
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

#   If more formatting possibilities needed (or more rows), choose from these:
#   'toolbar1': '''
#           fullscreen preview bold italic underline | fontselect,
#           fontsizeselect  | forecolor backcolor | alignleft alignright |
#           aligncenter alignjustify | indent outdent | bullist numlist table |
#           | link image media | codesample |
#           ''',
#   'toolbar2': '''
#           visualblocks visualchars |
#           charmap hr pagebreak nonbreaking anchor |  code |
#           ''',
    'contextmenu': 'formats | link',
    'menubar': True,
    'statusbar': True,
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Email config
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASS')

DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600 # default 2621440, 2.5MB -> 100MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000    # default 1000, was not enough for Mozambique Cyclone Idai data

timezone = pytz.timezone("Europe/Zurich")
PER_LAST_DUEDATE=timezone.localize(datetime(2018, 11, 15, 9, 59, 25, 0))
PER_NEXT_DUEDATE=timezone.localize(datetime(2023, 11, 15, 9, 59, 25, 0))

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
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '../server_errors.log',
            'formatter': 'timestamp',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
