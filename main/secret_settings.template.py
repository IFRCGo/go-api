import sys

SECRET_KEY = 'SECRET_KEY'

# Use sqlite for local tests, postgresql for everything else
if not os.environ.get('LOCAL_TEST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'name',
            'USER': 'user',
            'PASSWORD': 'password',
            'HOST': 'host',
            'PORT': '',
        }
    }
