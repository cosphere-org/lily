# -*- coding: utf-8 -*-

import os

from django.conf import settings


SECRET_KEY = 'not.really.needed'


DEBUG = True


ALLOWED_HOSTS = ["*"]


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOCS_TEST_EXAMPLES_FILE = os.path.join(BASE_DIR, 'docs', 'test_examples.json')

DOCS_OPEN_API_SPEC_FILE = os.path.join(BASE_DIR, 'docs', 'open_api_spec.json')

DOCS_COMMANDS_CONF_FILE = os.path.join(BASE_DIR, 'docs', 'commands_conf.json')

DOCS_MARKDOWN_SPEC_FILE = os.path.join(BASE_DIR, '../', 'DOCS.md')

LILY_AUTHORIZER_CLASS = getattr(
    settings,
    'LILY_AUTHORIZER_CLASS',
    'lily.base.authorizer.Authorizer')


# !!!!!!!!!!!!!!!!!
# FIXME: soon to be removed
#
# Contact / Email Sending Settings
#
EMAIL_SENDER_FROM = 'notification-no-reply@cosphere.org'


# FIXME: the below values would not be needed any more for the
# sender since all sending will be handled by the mailgun
EMAIL_SENDER_PASSWORD = 'fZGDSnKJT8q4UySM1'


EMAIL_SENDER_MAIL_SERVER_DOMAIN = 'smtp.gmail.com'


EMAIL_SENDER_MAIL_SERVER_SSL_PORT = 465


CONTACT_SEND_SECRET = (
    'Th)&PJ3*5PP:#3P7LDhn!VFnS;*>]Zx-y-b3ZD~fAF38RgH,*hCX]w^<L9mm`~e+')


CONTACT_SEND_CONFIRMATION_URL = os.environ.get("CONTACT_SEND_CONFIRMATION_URL")


CONTACT_CONFIRMATION_CODE_MAX_AGE = 3600 * 24 * 2


CONTACT_CONFIRMATION_SALT = 'FGkoFsfs'


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
