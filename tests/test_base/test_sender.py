# -*- coding: utf-8 -*-

from smtplib import SMTPException

from mock import call
import pytest

from lily.base import sender


def test_send__makes_the_right_calls(mocker):

    email_server_mock = mocker.patch('base.sender.email_server')
    mocker.patch('base.sender.settings.EMAIL_SENDER_FROM', 'test@ab.com')

    sendmail = email_server_mock.return_value.__enter__.return_value.sendmail

    sender.send('george@mailer.com', 'hi george!')

    assert (
        sendmail.call_args_list ==
        [call('test@ab.com', 'george@mailer.com', 'hi george!')])


def test_send__raises_error(mocker):

    logger_mock = mocker.patch('base.sender.logger')
    email_server_mock = mocker.patch('base.sender.email_server')
    sendmail_mock = (
        email_server_mock.return_value.__enter__.return_value.sendmail)
    sendmail_mock.side_effect = SMTPException

    with pytest.raises(sender.SendError) as cm:
        sender.send('george@mailer.com', 'hi george!')

    assert cm.value.args[0] == (
        "Error occurred while sending mail to george@mailer.com.")
    assert (
        logger_mock.exception.call_args_list ==
        [call("Error occurred while sending mail to george@mailer.com.")])
