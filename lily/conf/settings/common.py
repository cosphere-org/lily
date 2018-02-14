# -*- coding: utf-8 -*-

import os

#
# Internationalization
#
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


API_BASE_URI = os.environ.get('API_BASE_URI')


#
# Apps viewed and maintained by both Admin and API
#
INSTALLED_APPS = [
    'rest_framework',
    'docs',
    'account',
    'account_setting',
    'contact',
    'focus',
    'external',
    'payment',
]


#
# Environment Dependent Common Settings
#
if os.environ.get('USE_PROD_SETTINGS') or os.environ.get('USE_DEV_SETTINGS'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ.get('POSTGRES_DB'),
            'USER': os.environ.get('POSTGRES_USER'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
            'HOST': 'db',
            'PORT': '5432',
        },
    }

else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'cosphere_auth_service',
            'USER': 'maciej',
            'PASSWORD': '',
            'HOST': '127.0.0.1',
            'PORT': '5434',
        },
    }


#
# Templates are used by confirmation email mechanism as well as contact
# confirmation one. Also Admin part uses it for rendering of its own views.
#
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
