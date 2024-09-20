import base64
import logging
import os
import sys
from datetime import datetime

import environ
import pytz
from corsheaders.defaults import default_headers
from django.utils.translation import gettext_lazy as _
from urllib3.util.retry import Retry

from main import sentry

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

env = environ.Env(
    # Django
    DJANGO_DEBUG=(bool, False),
    DOCKER_HOST_IP=(str, None),
    DJANGO_SECRET_KEY=str,
    DJANGO_MEDIA_URL=(str, "/media/"),
    DJANGO_MEDIA_ROOT=(str, os.path.join(BASE_DIR, "media")),
    DJANGO_STATIC_URL=(str, "/static/"),
    DJANGO_STATIC_ROOT=(str, os.path.join(BASE_DIR, "static")),
    DJANGO_ADDITIONAL_ALLOWED_HOSTS=(list, []),  # Eg: api.go.ifrc.org, goadmin.ifrc.org, dsgocdnapi.azureedge.net
    GO_ENVIRONMENT=(str, "development"),  # staging, production
    #
    API_FQDN=str,  # sub-domain.domain.domain-extension
    FRONTEND_URL=str,
    # Database
    DJANGO_DB_NAME=str,
    DJANGO_DB_USER=str,
    DJANGO_DB_PASS=str,
    DJANGO_DB_HOST=str,
    DJANGO_DB_PORT=(int, 5432),
    # Azure storage
    AZURE_STORAGE_ACCOUNT=(str, None),
    AZURE_STORAGE_KEY=(str, None),
    # Email
    EMAIL_API_ENDPOINT=(str, None),
    EMAIL_HOST=(str, None),
    EMAIL_PORT=(str, None),
    EMAIL_USER=(str, None),
    EMAIL_PASS=(str, None),
    DEBUG_EMAIL=(bool, False),  # This was 0/1 before
    # TEST_EMAILS=(list, ['im@ifrc.org']), # maybe later
    # Translation
    # Translator Available:
    #   - lang.translation.DummyTranslator
    #   - lang.translation.IfrcTranslator
    #   - lang.translation.AmazonTranslator
    AUTO_TRANSLATION_TRANSLATOR=(str, "lang.translation.DummyTranslator"),
    # AWS Translate NOTE: not used right now
    AWS_TRANSLATE_ACCESS_KEY=(str, None),
    AWS_TRANSLATE_SECRET_KEY=(str, None),
    AWS_TRANSLATE_REGION=(str, None),
    # IFRC Translation
    IFRC_TRANSLATION_DOMAIN=(str, None),  # https://example.ifrc.org
    IFRC_TRANSLATION_GET_API_KEY=(str, None),
    IFRC_TRANSLATION_HEADER_API_KEY=(str, None),
    # Celery NOTE: Not used right now
    CELERY_REDIS_URL=str,
    CACHE_REDIS_URL=str,
    CACHE_TEST_REDIS_URL=(str, None),
    CACHE_MIDDLEWARE_SECONDS=(int, None),
    # MOLNIX
    MOLNIX_API_BASE=(str, "https://api.ifrc-staging.rpm.molnix.com/api/"),
    MOLNIX_USERNAME=(str, None),
    MOLNIX_PASSWORD=(str, None),
    # ERP
    ERP_API_ENDPOINT=(str, "https://ifrctintapim001.azure-api.net/GoAPI/ExtractGoEmergency"),
    ERP_API_SUBSCRIPTION_KEY=(str, "abcdef"),
    # Misc
    FDRS_APIKEY=(str, None),
    FDRS_CREDENTIAL=(str, None),
    HPC_CREDENTIAL=(str, None),
    APPLICATION_INSIGHTS_INSTRUMENTATION_KEY=(str, None),
    # Pytest (Only required when running tests)
    PYTEST_XDIST_WORKER=(str, None),
    # Elastic-Cache
    ELASTIC_SEARCH_HOST=(str, None),
    ELASTIC_SEARCH_INDEX=(str, "new_index"),
    ELASTIC_SEARCH_TEST_INDEX=(str, "new_test_index"),  # This will be used and cleared by test
    # FTP
    GO_FTPHOST=(str, None),
    GO_FTPUSER=(str, None),
    GO_FTPPASS=(str, None),
    GO_DBPASS=(str, None),
    # Appeal Server Credentials (https://go-api.ifrc.org/api/)
    APPEALS_USER=(str, None),
    APPEALS_PASS=(str, None),
    # Sentry
    SENTRY_DSN=(str, None),
    SENTRY_SAMPLE_RATE=(float, 0.2),
    # Maintenance mode
    DJANGO_READ_ONLY=(bool, False),
    # Misc
    DISABLE_API_CACHE=(bool, False),
    # jwt private and public key
    JWT_PRIVATE_KEY_BASE64_ENCODED=(str, None),
    JWT_PUBLIC_KEY_BASE64_ENCODED=(str, None),
    JWT_PRIVATE_KEY=(str, None),
    JWT_PUBLIC_KEY=(str, None),
    JWT_EXPIRE_TIMESTAMP_DAYS=(int, 365),
    # Country page
    NS_CONTACT_USERNAME=(str, None),
    NS_CONTACT_PASSWORD=(str, None),
    ACAPS_API_TOKEN=(str, None),
    NS_DOCUMENT_API_KEY=(str, None),
    NS_INITIATIVES_API_KEY=(str, None),
    NS_INITIATIVES_API_TOKEN=(str, None),
)


# Requires uppercase variable https://docs.djangoproject.com/en/2.1/topics/settings/#creating-your-own-settings
BASE_URL = GO_API_FQDN = env("API_FQDN")

INTERNAL_IPS = ["127.0.0.1"]
if env("DOCKER_HOST_IP"):
    INTERNAL_IPS.append(env("DOCKER_HOST_IP"))

DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": [
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
    ],
}

ALLOWED_HOSTS = [
    "localhost",
    "0.0.0.0",
    GO_API_FQDN,
    *env("DJANGO_ADDITIONAL_ALLOWED_HOSTS"),
]

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
GO_ENVIRONMENT = env("GO_ENVIRONMENT")

# See if we are inside a test environment
TESTING = (
    any(
        [
            arg in sys.argv
            for arg in [
                "test",
                "pytest",
                "py.test",
                "/usr/local/bin/pytest",
                "/usr/local/bin/py.test",
                "/usr/local/lib/python3.6/dist-packages/py/test.py",
            ]
            # Provided by pytest-xdist (If pytest is used)
        ]
    )
    or env("PYTEST_XDIST_WORKER") is not None
)


GO_APPS = [
    "api",
    "per",
    "notifications",
    "registrations",
    "deployments",
    "databank",
    "lang",
    "dref",
    "flash_update",
    "eap",
    "country_plan",
    "local_units",
]

INSTALLED_APPS = [
    # External App (This app has to defined before django.contrib.admin)
    "modeltranslation",  # https://django-modeltranslation.readthedocs.io/en/latest/installation.html#installed-apps
    "drf_spectacular",
    # Django Apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_admin_listfilter_dropdown",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "guardian",
    "django_filters",
    "django_read_only",
    # GO Apps
    *GO_APPS,
    # Utils Apps
    "tinymce",
    "admin_auto_filters",
    "haystack",
    # Logging
    "reversion",
    "reversion_compare",
    # Debug
    "debug_toolbar",
    # GIS
    "django.contrib.gis",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "EXCEPTION_HANDLER": "main.exception_handler.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
        "rest_framework_csv.renderers.PaginatedCSVRenderer",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    # 'middlewares.middlewares.LocaleMiddleware',
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # 'middlewares.cache.UpdateCacheForUserMiddleware',
    "django.middleware.common.CommonMiddleware",
    # 'middlewares.cache.FetchFromCacheForUserMiddleware',
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "middlewares.middlewares.RequestMiddleware",
    "reversion.middleware.RevisionMiddleware",
]

AUTHENTICATION_BACKENDS = (
    # 'django.contrib.auth.backends.ModelBackend',
    "api.authentication_backend.EmailBackend",
    "guardian.backends.ObjectPermissionBackend",
)

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    "sentry-trace",
    "baggage",
]

ROOT_URLCONF = "main.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "notifications/templates/"),
            os.path.join(BASE_DIR, "api/templates/"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "main.context_processors.ifrc_go",
            ],
        },
    },
]

WSGI_APPLICATION = "main.wsgi.application"

# Use local postgres for dev, env-determined for production
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("DJANGO_DB_NAME"),
        "USER": env("DJANGO_DB_USER"),
        "PASSWORD": env("DJANGO_DB_PASS"),
        "HOST": env("DJANGO_DB_HOST"),
        "PORT": env("DJANGO_DB_PORT"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "main.validators.NumberValidator",
    },
    {
        "NAME": "main.validators.UppercaseValidator",
    },
    {
        "NAME": "main.validators.LowercaseValidator",
    },
    {
        "NAME": "main.validators.SymbolValidator",
    },
]

TINYMCE_DEFAULT_CONFIG = {
    "entity_encoding": "raw",
    "height": 360,
    "width": 1120,
    "cleanup_on_startup": True,
    "custom_undo_redo_levels": 20,
    "plugins": '''
        anchor autolink charmap code codesample directionality
        fullscreen image insertdatetime link lists media
        nonbreaking pagebreak preview save searchreplace table
        visualblocks visualchars
        """,
    "toolbar1": """
        bold italic underline superscript subscript fontsizeselect
        | alignleft alignright | aligncenter alignjustify
        | indent outdent | bullist numlist |
        | link visualchars charmap hr nonbreaking | code preview fullscreen
        """,
    "force_p_newlines": True,  # TODO: could be False?
    "force_br_newlines": True,  # TODO: could be False?
    "forced_root_block": "",
    "contextmenu": "formats | link",
    "menubar": False,
    "statusbar": False,
    # https://www.tiny.cloud/docs/configure/content-filtering/#invalid_styles
    "invalid_styles": {"*": "opacity"},  # Global invalid style
    # 'extended_valid_elements': 'iframe[src|frameborder|style|scrolling|class|width|height|name|align]',
    # If more formatting possibilities needed (or more rows), choose from these:
    # 'toolbar1': ''',
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

# Languages using BiDi (right-to-left) layout
LANGUAGES_BIDI = ["he", "ar", "ar-dz", "ckb", "fa", "ug", "ur"]

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Make sure to update main.translation if this is updated
LANGUAGES = (
    ("en", _("English")),
    ("es", _("Spanish")),
    ("fr", _("French")),
    ("ar", _("Arabic")),
)
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_FALLBACK_LANGUAGES = ("en", "fr", "es", "ar")
AUTO_TRANSLATION_TRANSLATOR = env("AUTO_TRANSLATION_TRANSLATOR")

IFRC_TRANSLATION_DOMAIN = env("IFRC_TRANSLATION_DOMAIN")
IFRC_TRANSLATION_GET_API_KEY = env("IFRC_TRANSLATION_GET_API_KEY")
IFRC_TRANSLATION_HEADER_API_KEY = env("IFRC_TRANSLATION_HEADER_API_KEY")

MEDIA_URL = env("DJANGO_MEDIA_URL")
MEDIA_ROOT = env("DJANGO_MEDIA_ROOT")

STATIC_URL = env("DJANGO_STATIC_URL")
STATIC_ROOT = env("DJANGO_STATIC_ROOT")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "go-static"),
]

# Needed to generate correct https links when running behind a reverse proxy
# when SSL is terminated at the proxy
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_SCHEME", "https")

AZURE_STORAGE_ACCOUNT = env("AZURE_STORAGE_ACCOUNT")
AZURE_STORAGE_KEY = env("AZURE_STORAGE_KEY")

AZURE_STORAGE = {
    "CONTAINER": "api",
    "ACCOUNT_NAME": AZURE_STORAGE_ACCOUNT,
    "ACCOUNT_KEY": AZURE_STORAGE_KEY,
    "CDN_HOST": None,
    "USE_SSL": False,
}
if AZURE_STORAGE_ACCOUNT:
    DEFAULT_FILE_STORAGE = "api.storage.AzureStorage"

"""
# FIXME: TODO: Use this instead. https://django-storages.readthedocs.io/en/latest/backends/azure.html
AZURE_ACCOUNT_NAME = env('AZURE_STORAGE_ACCOUNT')
AZURE_ACCOUNT_KEY = env('AZURE_STORAGE_KEY')
AZURE_CONTAINER = 'api'
if AZURE_STORAGE_ACCOUNT:
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
"""

# Email config
EMAIL_API_ENDPOINT = env("EMAIL_API_ENDPOINT")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USER = env("EMAIL_USER")
EMAIL_PASS = env("EMAIL_PASS")
DEBUG_EMAIL = env("DEBUG_EMAIL")
# TEST_EMAILS = env('TEST_EMAILS') # maybe later

DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # default 2621440, 2.5MB -> 100MB
# default 1000, was not enough for Mozambique Cyclone Idai data
# second  2000, was not enouch for Global COVID Emergency

# See: https://github.com/IFRCGo/go-api/issues/1127
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

timezone = pytz.timezone("Europe/Zurich")
PER_LAST_DUEDATE = timezone.localize(datetime(2018, 11, 15, 9, 59, 25, 0))
PER_NEXT_DUEDATE = timezone.localize(datetime(2023, 11, 15, 9, 59, 25, 0))

FDRS_APIKEY = env("FDRS_APIKEY")
FDRS_CREDENTIAL = env("FDRS_CREDENTIAL")
HPC_CREDENTIAL = env("HPC_CREDENTIAL")

APPLICATION_INSIGHTS_INSTRUMENTATION_KEY = env("APPLICATION_INSIGHTS_INSTRUMENTATION_KEY")

if not TESTING and APPLICATION_INSIGHTS_INSTRUMENTATION_KEY:
    MIDDLEWARE.append("opencensus.ext.django.middleware.OpencensusMiddleware")
    OPENCENSUS = {
        "TRACE": {
            "SAMPLER": "opencensus.trace.samplers.ProbabilitySampler(rate=1)",
            "EXPORTER": """opencensus.ext.azure.trace_exporter.AzureExporter(
                connection_string="InstrumentationKey={}",
                enable_local_storage=False,
            )""".format(
                APPLICATION_INSIGHTS_INSTRUMENTATION_KEY
            ),
        }
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "timestamp": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "api.filehandler.MakeFileHandler",
            "filename": "../logs/logger.log",
            "formatter": "timestamp",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
        },
        "celery": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

if DEBUG:

    def log_render_extra_context(record):
        """
        Append extra->context to logs
        NOTE: This will appear in logs when used with logger.xxx(..., extra={'context': {..content}})
        NOTE: This is also send to sentry which can provide additional context to the issue
        """
        if hasattr(record, "context"):
            record.context = f" - {str(record.context)}"
        else:
            record.context = ""
        return True

    LOGGING = {
        **LOGGING,
        "filters": {
            **LOGGING.get("filters", {}),
            "render_extra_context": {
                "()": "django.utils.log.CallbackFilter",
                "callback": log_render_extra_context,
            },
        },
        "formatters": {
            **LOGGING.get("formatters", {}),
            "console": {
                "()": "colorlog.ColoredFormatter",
                "format": (
                    "%(log_color)s%(levelname)-8s%(red)s%(module)-8s%(reset)s %(asctime)s %(blue)s%(message)s %(context)s"
                ),
            },
        },
        "handlers": {
            **LOGGING.get("handlers", {}),
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "filters": ["render_extra_context"],
                "formatter": "console",
            },
        },
        "loggers": {
            **LOGGING.get("loggers", {}),
            **{
                app: {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                }
                for app in GO_APPS
            },
        },
    }

# AWS Translate Credentials
AWS_TRANSLATE_ACCESS_KEY = env("AWS_TRANSLATE_ACCESS_KEY")
AWS_TRANSLATE_SECRET_KEY = env("AWS_TRANSLATE_SECRET_KEY")
AWS_TRANSLATE_REGION = env("AWS_TRANSLATE_REGION")

TEST_RUNNER = "snapshottest.django.TestRunner"

# CELERY CONFIG
CELERY_REDIS_URL = env("CELERY_REDIS_URL")  # "redis://:{password}@{host}:{port}/{db}"
CELERY_BROKER_URL = CELERY_REDIS_URL
CELERY_RESULT_BACKEND = CELERY_REDIS_URL
CELERY_TIMEZONE = TIME_ZONE
CELERY_ACKS_LATE = True

RETRY_STRATEGY = Retry(total=3, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS"])

MOLNIX_API_BASE = env("MOLNIX_API_BASE")
MOLNIX_USERNAME = env("MOLNIX_USERNAME")
MOLNIX_PASSWORD = env("MOLNIX_PASSWORD")

ERP_API_ENDPOINT = env("ERP_API_ENDPOINT")
ERP_API_SUBSCRIPTION_KEY = env("ERP_API_SUBSCRIPTION_KEY")

TEST_DIR = os.path.join(BASE_DIR, "main/test_files")

# Elastic search host
ELASTIC_SEARCH_HOST = env("ELASTIC_SEARCH_HOST")
ELASTIC_SEARCH_INDEX = env("ELASTIC_SEARCH_INDEX")
ELASTIC_SEARCH_TEST_INDEX = env("ELASTIC_SEARCH_TEST_INDEX")

# FTP
GO_FTPHOST = env("GO_FTPHOST")
GO_FTPUSER = env("GO_FTPUSER")
GO_FTPPASS = env("GO_FTPPASS")
GO_DBPASS = env("GO_DBPASS")

# MISC
FRONTEND_URL = env("FRONTEND_URL")

# COUNTRY PAGE
NS_CONTACT_USERNAME = env("NS_CONTACT_USERNAME")
NS_CONTACT_PASSWORD = env("NS_CONTACT_PASSWORD")
ACAPS_API_TOKEN = env("ACAPS_API_TOKEN")
NS_DOCUMENT_API_KEY = env("NS_DOCUMENT_API_KEY")
NS_INITIATIVES_API_KEY = env("NS_INITIATIVES_API_KEY")
NS_INITIATIVES_API_TOKEN = env("NS_INITIATIVES_API_TOKEN")

DREF_OP_UPDATE_FINAL_REPORT_UPDATE_ERROR_MESSAGE = "OBSOLETE_PAYLOAD"

# Appeal Server Credentials
APPEALS_USER = env("APPEALS_USER")
APPEALS_PASS = env("APPEALS_PASS")

# Handmade Git Command
LAST_GIT_TAG = max(os.listdir(os.path.join(BASE_DIR, ".git", "refs", "tags")), default=0)

# Sentry Config
SENTRY_DSN = env("SENTRY_DSN")
SENTRY_SAMPLE_RATE = env("SENTRY_SAMPLE_RATE")

SENTRY_CONFIG = {
    "dsn": SENTRY_DSN,
    "send_default_pii": True,
    "traces_sample_rate": SENTRY_SAMPLE_RATE,
    "enable_tracing": True,
    "release": sentry.fetch_git_sha(BASE_DIR),
    "environment": GO_ENVIRONMENT,
    "debug": DEBUG,
    "tags": {
        "site": GO_API_FQDN,
    },
}
if SENTRY_DSN:
    sentry.init_sentry(
        app_type="API",
        **SENTRY_CONFIG,
    )
# Required for Django HayStack
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine",
        "URL": ELASTIC_SEARCH_HOST,
        "INDEX_NAME": ELASTIC_SEARCH_INDEX,
    },
}

HAYSTACK_LIMIT_TO_REGISTERED_MODELS = False

SUSPEND_SIGNALS = True

# Maintenance mode
DJANGO_READ_ONLY = env("DJANGO_READ_ONLY")

CACHE_REDIS_URL = env("CACHE_REDIS_URL")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("CACHE_REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

if env("CACHE_MIDDLEWARE_SECONDS"):
    CACHE_MIDDLEWARE_SECONDS = env("CACHE_MIDDLEWARE_SECONDS")  # Planned: 600 for staging, 60 from prod
DISABLE_API_CACHE = env("DISABLE_API_CACHE")

SPECTACULAR_SETTINGS = {
    "TITLE": "IFRC-GO API",
    "DESCRIPTION": 'Please see the <a href="https://go-wiki.ifrc.org/en/go-api/api-overview" target="_blank">GO Wiki</a> for an overview of API usage, or the interactive <a href="/api-docs/swagger-ui/" target="_blank">Swagger page</a>.',  # noqa: E501
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE": False,
    "ENUM_NAME_OVERRIDES": {},
}

# A character which is rarely used in strings – for separator:
SEP = "¤"


def decode_base64(env_key, fallback_env_key):
    if encoded_value := env(env_key):
        # TODO: Instead use docker/k8 secrets file mount?
        try:
            return base64.b64decode(encoded_value)
        except Exception:
            logger.error(f"Failed to decode {env_key}", exc_info=True)
    return env(fallback_env_key)


JWT_PRIVATE_KEY = decode_base64("JWT_PRIVATE_KEY_BASE64_ENCODED", "JWT_PRIVATE_KEY")
JWT_PUBLIC_KEY = decode_base64("JWT_PUBLIC_KEY_BASE64_ENCODED", "JWT_PUBLIC_KEY")
JWT_EXPIRE_TIMESTAMP_DAYS = env("JWT_EXPIRE_TIMESTAMP_DAYS")

# Need to load this to overwrite modeltranslation module
import main.translation  # noqa: F401 E402
