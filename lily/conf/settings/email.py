# -*- coding: utf-8 -*-

import os


# ================================
# Contact / Email Sending Settings
# ================================
EMAIL_SENDER_FROM = 'notification-no-reply@cosphere.org'


# FIXME: the below values would not be needed any more for the
# sender since all sending will be handled by the mailgun
EMAIL_SENDER_PASSWORD = 'fZGDSnKJT8q4UySM1'


EMAIL_SENDER_MAIL_SERVER_DOMAIN = 'smtp.gmail.com'


EMAIL_SENDER_MAIL_SERVER_SSL_PORT = 465


# EMAIL_SENDER_MAIL_SERVER_TLS_PORT = 587


CONTACT_SEND_SECRET = (
    'Th)&PJ3*5PP:#3P7LDhn!VFnS;*>]Zx-y-b3ZD~fAF38RgH,*hCX]w^<L9mm`~e+')


CONTACT_SEND_CONFIRMATION_URL = os.environ.get("CONTACT_SEND_CONFIRMATION_URL")


CONTACT_CONFIRMATION_CODE_MAX_AGE = 3600 * 24 * 2


CONTACT_CONFIRMATION_SALT = 'FGkoFsfs'
