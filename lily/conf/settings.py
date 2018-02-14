# -*- coding: utf-8 -*-

import os

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# FIXME: soon to be removed!!!
from .settings.email import *  # noqa
from .settings.docs import *  # noqa


SECRET_KEY = 'not.really.needed'


DEBUG = True


ALLOWED_HOSTS = ["*"]


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
