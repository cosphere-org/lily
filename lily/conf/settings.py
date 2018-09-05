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
LILY_PROJECT_BASE = getattr(
    settings,
    'LILY_PROJECT_BASE',
    os.path.dirname(BASE_DIR))

LILY_CONFIG_FILE_PATH = os.path.join(
    LILY_PROJECT_BASE, 'lily/conf/config.yaml')

LILY_CACHE_DIR = os.path.join(BASE_DIR, '.commands')

LILY_CACHE_TTL = getattr(settings, 'LILY_CACHE_TTL', 10 * 60)  # 10 minutes

LILY_MAX_DOMAIN_ID_LENGTH = getattr(
    settings, 'LILY_MAX_DOMAIN_ID_LENGTH', 32)

LILY_DOCS_MARKDOWN_SPEC_FILE = getattr(
    settings,
    'LILY_DOCS_MARKDOWN_SPEC_FILE',
    os.path.join(LILY_PROJECT_BASE, 'DOCS.md'))
#
# AUTHORIZER
#
LILY_AUTHORIZER_CLASS = getattr(
    settings,
    'LILY_AUTHORIZER_CLASS',
    'lily.base.authorizer.Authorizer')

#
# DOCS
#
LILY_ANGULAR_CLIENT_ORIGIN = 'git@bitbucket.org:goodai/lily-angular-client.git'

#
# ENTRYPOINT
#
LILY_ENTRYPOINT_VIEWS_ACCESS_LIST = getattr(
    settings,
    'LILY_ENTRYPOINT_VIEWS_ACCESS_LIST',
    None)

# LILY_COMMAND_ENTRYPOINTS = []
LILY_COMMAND_ENTRYPOINTS = [
    'http://localhost:7000',
]

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
# Language Detection API Key
# To be replaced by in-house solution which doesn't have to travel over the
# network !!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
DETECT_LANGUAGE_API_KEY = getattr(
    settings,
    'DETECT_LANGUAGE_API_KEY',
    'fake.key')

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
    'repo',
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
