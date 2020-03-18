
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

# FIXME: !!!! should be moved to github!
LILY_ANGULAR_CLIENT_ORIGIN = (
    'git@bitbucket.org:goodai/lily-angular-client.git')
# git@bitbucket.org:goodai/lily-angular-client-base.git

# FIXME: !!!! should be moved to github!
LILY_ANGULAR_HTTP_ORIGIN = (
    'git@bitbucket.org:goodai/lily-angular-http.git')

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
        'USER': 'local',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '5434',
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
