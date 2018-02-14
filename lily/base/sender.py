# -*- coding: utf-8 -*-

from contextlib import contextmanager
import logging
import smtplib

from django.conf import settings


logger = logging.getLogger()


class SendError(Exception):
    """
    General Error raised whenever any problems with sending email occur.

    """


@contextmanager
def email_server():

    # server = smtplib.SMTP(settings.EMAIL_SENDER_MAIL_SERVER)

    server = smtplib.SMTP_SSL(
        settings.EMAIL_SENDER_MAIL_SERVER_DOMAIN,
        settings.EMAIL_SENDER_MAIL_SERVER_SSL_PORT)
    # server.starttls()

    server.login(settings.EMAIL_SENDER_FROM, settings.EMAIL_SENDER_PASSWORD)
    yield server
    server.quit()


def send(to, message):
    try:
        with email_server() as server:
            server.sendmail(settings.EMAIL_SENDER_FROM, to, message)

    except smtplib.SMTPException:
        msg = "Error occurred while sending mail to {0}.".format(to)
        logger.exception(msg)
        raise SendError(msg)
