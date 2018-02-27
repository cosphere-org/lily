# -*- coding: utf-8 -*-

import os

from django.conf import settings


SECRET_KEY = 'not.really.needed'


DEBUG = True


ALLOWED_HOSTS = ["*"]


#
# LILY SPECIFIC SETTINGS
#
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LILY_DOCS_TEST_EXAMPLES_FILE = os.path.join(
    BASE_DIR, 'docs', 'test_examples.json')

LILY_DOCS_OPEN_API_SPEC_FILE = os.path.join(
    BASE_DIR, 'docs', 'open_api_spec.json')

LILY_DOCS_COMMANDS_CONF_FILE = os.path.join(
    BASE_DIR, 'docs', 'commands_conf.json')

LILY_DOCS_MARKDOWN_SPEC_FILE = os.path.join(
    BASE_DIR, '../', 'DOCS.md')

LILY_AUTHORIZER_CLASS = getattr(
    settings,
    'LILY_AUTHORIZER_CLASS',
    'lily.base.authorizer.Authorizer')

LILY_PROJECT_BASE = os.path.dirname(BASE_DIR)

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
    'django.contrib.contenttypes',
    'django.contrib.auth',
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'index.db'),
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
