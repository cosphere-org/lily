# -*- coding: utf-8 -*-

import os

from django.conf import settings


SECRET_KEY = 'not.really.needed'


DEBUG = True


ALLOWED_HOSTS = ["*"]


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


#
# LILY SPECIFIC SETTINGS
#

#
# GENERAL
#
LILY_PROJECT_BASE = os.path.dirname(BASE_DIR)

LILY_SERVICE_NAME = 'LILY_SERVICE'

LILY_SERVICE_VERSION = '0.1.4.whatever'

LILY_SERVICE_REPOSITORY_URI = 'https://bitbucket.org/goodai/lily'

#
# AUTHORIZER
#
LILY_AUTHORIZER_CLASS = getattr(
    settings,
    'LILY_AUTHORIZER_CLASS',
    'lily.base.authorizer.Authorizer')

#
# ENTRYPOINT
#
LILY_ENTRYPOINT_VIEWS_ACCESS_LIST = None

#
# DOCS
#
LILY_DOCS_BASE_DIR = os.path.join(BASE_DIR, './.docs')

LILY_DOCS_VIEWS_ACCESS_LIST = None

# !!!! DEPRECATED
# FIXME: !!!!!!!!!!!!!!
# -- replace with some generic stuff
LILY_DOCS_TEST_EXAMPLES_FILE = os.path.join(
    BASE_DIR, 'docs', 'test_examples.json')

# !!!! DEPRECATED
# FIXME: !!!!!!!!!!!!!!
LILY_DOCS_OPEN_API_SPEC_FILE = os.path.join(
    BASE_DIR, 'docs', 'open_api_spec.json')

# !!!! DEPRECATED
# FIXME: !!!!!!!!!!!!!!
LILY_DOCS_COMMANDS_CONF_FILE = os.path.join(
    BASE_DIR, 'docs', 'commands_conf.json')

# !!!! DEPRECATED
# FIXME: !!!!!!!!!!!!!!
LILY_DOCS_MARKDOWN_SPEC_FILE = os.path.join(
    BASE_DIR, '../', 'DOCS.md')

#
# ASYNC
#
LILY_ASYNC_LOCK_DB_HOST = 'localhost'

LILY_ASYNC_LOCK_DB_PORT = 6379

LILY_ASYNC_LOCK_DB_INDEX = 1

#
# Language Detection API Key
# To be replaced by in-house solution which doesn't have to travel over the
# network !!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
DETECT_LANGUAGE_API_KEY = 'fake.key'

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
    'django.contrib.contenttypes',
    'django.contrib.auth',
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'lily',
        'USER': 'maciej',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '5434',
    },
}


MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]


ROOT_URLCONF = 'conf.urls'


WSGI_APPLICATION = 'conf.wsgi.application'


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
