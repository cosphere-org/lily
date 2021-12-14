
from django.conf import settings


SECRET_KEY = 'not.really.needed'


DEBUG = True


ALLOWED_HOSTS = ["*"]


#
# LILY SPECIFIC SETTINGS
#
LILY_AUTHORIZER_CLASS = getattr(
    settings,
    'LILY_AUTHORIZER_CLASS',
    'lily.base.authorizer.BaseAuthorizer')


LILY_AUTHORIZER_ACCESS_ENUM_CLASS = getattr(
    settings,
    'LILY_AUTHORIZER_ACCESS_ENUM_CLASS',
    'AccountType')


LILY_ENTRYPOINT_COMMANDS_ACCESS_LIST = getattr(
    settings,
    'LILY_ENTRYPOINT_COMMANDS_ACCESS_LIST',
    None)


LILY_EXCLUDE_QUERY_PARSER_ALL_OPTIONAL_ASSERTIONS = getattr(
    settings,
    'LILY_EXCLUDE_QUERY_PARSER_ALL_OPTIONAL_ASSERTIONS',
    None)

LILY_ANGULAR_CLIENT_ORIGIN = getattr(
    settings,
    'LILY_ANGULAR_CLIENT_ORIGIN',
    'https://github.com/cosphere-org/lily-angular-client-base.git')

#
# TEST
#
LILY_TEST_CLIENT_TYPE = getattr(
    settings,
    'LILY_TEST_CLIENT_TYPE',
    'UNIT')

LILY_TEST_CLIENT_VERIFY_SSL = getattr(
    settings,
    'LILY_TEST_CLIENT_VERIFY_SSL',
    False)

LILY_TEST_CLIENT_BASE_URI = getattr(
    settings,
    'LILY_TEST_CLIENT_BASE_URI',
    'http://localhost:8000')

#
# ASYNC
#
LILY_ASYNC_LOCK_DB_HOST = getattr(
    settings,
    'LILY_ASYNC_LOCK_DB_HOST',
    'localhost')

LILY_ASYNC_LOCK_DB_PORT = getattr(
    settings,
    'LILY_ASYNC_LOCK_DB_PORT',
    6379)

LILY_ASYNC_LOCK_DB_INDEX = getattr(
    settings,
    'LILY_ASYNC_LOCK_DB_INDEX',
    1)

#
# Internationalization
#
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


#
# Apps viewed and maintained by both Admin and API
#
INSTALLED_APPS = [
    'rest_framework',

    'docs',
    'base',
    'search',
    'entrypoint',
    'assertion',
    'migrator',

    'django.contrib.contenttypes',
    'django.contrib.auth',
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'lily',
        'USER': 'lily',
        'PASSWORD': 'mysecret',
        'HOST': '127.0.0.1',
        'PORT': '5435',
    },
}


MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]


ROOT_URLCONF = getattr(
    settings,
    'ROOT_URLCONF',
    'conf.urls')


WSGI_APPLICATION = getattr(
    settings,
    'WSGI_APPLICATION',
    'conf.wsgi.application')


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [],
        },
    },
]
