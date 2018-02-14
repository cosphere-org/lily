# -*- coding: utf-8 -*-

import json

from django.http.request import HttpRequest

from cosphere_base_service.base.response import (
    JsonResponse,
    JsonCreated,
    JsonAuthError,
    JsonAccessDenied,
    JsonBrokenPayload,
    JsonDoesNotExist,
    JsonServerError,
)


# -- Auth Events
ACCESS_DENIED = 'ACCESS_DENIED'
AUTH_TOKEN_WAS_BROKEN = 'AUTH_TOKEN_WAS_BROKEN'
COULD_NOT_FIND_AUTH_TOKEN = 'COULD_NOT_FIND_AUTH_TOKEN'
AUTH_TOKEN_WAS_MISSING_FIELDS = 'AUTH_TOKEN_WAS_MISSING_FIELDS'
INVALID_ACCOUNT_TYPE_USED = 'INVALID_ACCOUNT_TYPE_USED'
AUTHENTICATED = 'AUTHENTICATED'

# -- Generic Events
BODY_JSON_DID_NOT_PARSE = 'BODY_JSON_DID_NOT_PARSE'
BODY_DID_NOT_VALIDATE = 'BODY_DID_NOT_VALIDATE'
QUERY_DID_NOT_VALIDATE = 'QUERY_DID_NOT_VALIDATE'
RESPONSE_DID_NOT_VALIDATE = 'RESPONSE_DID_NOT_VALIDATE'

# -- Accounts
ACCOUNT_MARKED_FOR_DOWNGRADE = 'ACCOUNT_MARKED_FOR_DOWNGRADE'
ACCOUNT_DOWNGRADED = 'ACCOUNT_DOWNGRADED'
ACCOUNT_UPGRADED = 'ACCOUNT_UPGRADED'
PROTECTED_ACCOUNT_UPGRADE_ATTEMPTED = 'PROTECTED_ACCOUNT_UPGRADE_ATTEMPTED'
PROTECTED_ACCOUNT_DOWNGRADE_ATTEMPTED = 'PROTECTED_ACCOUNT_DOWNGRADE_ATTEMPTED'
WEAKER_ACCOUNT_UPGRADE_ATTEMPTED = 'WEAKER_ACCOUNT_UPGRADE_ATTEMPTED'
STRONGER_ACCOUNT_DOWNGRADE_ATTEMPTED = 'STRONGER_ACCOUNT_DOWNGRADE_ATTEMPTED'
DOWNGRADE_DATETIME_NOT_IN_FUTURE_DETECTED = (
    'DOWNGRADE_DATETIME_NOT_IN_FUTURE_DETECTED')
DOWNGRADE_DATETIME_NOT_UTC_DETECTED = 'DOWNGRADE_DATETIME_NOT_UTC_DETECTED'
DOWNGRADE_WITH_BROKEN_DATA_ATTEMPTED = 'DOWNGRADE_WITH_BROKEN_DATA_ATTEMPTED'

# -- Does Not Exist Events
COULD_NOT_FIND_USER = 'COULD_NOT_FIND_USER'
COULD_NOT_FIND_ACCOUNT = 'COULD_NOT_FIND_ACCOUNT'
COULD_NOT_FIND_PRODUCT = 'COULD_NOT_FIND_PRODUCT'
COULD_NOT_FIND_PAYMENT = 'COULD_NOT_FIND_PAYMENT'
COULD_NOT_FIND_PAYMENT_CARD = 'COULD_NOT_FIND_PAYMENT_CARD'
COULD_NOT_FIND_DEFAULT_PAYMENT_CARD = 'COULD_NOT_FIND_DEFAULT_PAYMENT_CARD'
FOUND_MULTIPLE_DEFAULT_PAYMENT_CARD = 'FOUND_MULTIPLE_DEFAULT_PAYMENT_CARD'

# -- Create Errors Events
COULD_NOT_CREATE_PAYMENT_BROKEN_SIGNATURE = (
    'COULD_NOT_CREATE_PAYMENT_BROKEN_SIGNATURE')

COULD_NOT_CREATE_PAYMENT_BROKEN_SIGNATURE = (
    'COULD_NOT_CREATE_PAYMENT_BROKEN_SIGNATURE')

COULD_NOT_CREATE_PAYMENT_SESSION_ID_ERROR = (
    'COULD_NOT_CREATE_PAYMENT_SESSION_ID_ERROR')

COULD_NOT_CREATE_PAYMENT_CARD_BROKEN_DATA = (
    'COULD_NOT_CREATE_PAYMENT_CARD_BROKEN_DATA')

COULD_NOT_CREATE_PAYMENT_CARD_PAYMENT_PROVIDER_ERROR = (
    'COULD_NOT_CREATE_PAYMENT_CARD_PAYMENT_PROVIDER_ERROR')

# -- External Payment Provider Errors
COULD_NOT_AUTHENTICATE_TO_PAYMENT_PROVIDER_BAD_STATUS_CODE = (
    'COULD_NOT_AUTHENTICATE_TO_PAYMENT_PROVIDER_BAD_STATUS_CODE')

COULD_NOT_AUTHENTICATE_TO_PAYMENT_PROVIDER_NO_TOKEN = (
    'COULD_NOT_AUTHENTICATE_TO_PAYMENT_PROVIDER_NO_TOKEN')

# -- Warnings
MISSING_COMMAND_LINK_PARAMS_DETECTED = 'MISSING_COMMAND_LINK_PARAMS_DETECTED'

# -- Payment Cards
PAYMENT_CARD_CREATED = 'PAYMENT_CARD_CREATED'
PAYMENT_CARDS_LISTED = 'PAYMENT_CARDS_LISTED'
PAYMENT_CARD_REMOVED = 'PAYMENT_CARD_REMOVED'
PAYMENT_CARD_MARKED_AS_DEFAULT = 'PAYMENT_CARD_MARKED_AS_DEFAULT'
PAYMENT_CARD_WIDGET_RENDERED = 'PAYMENT_CARD_WIDGET_RENDERED'

# -- Payment
PAYMENT_STATUS_UPDATE_IS_BROKEN = 'PAYMENT_STATUS_UPDATE_IS_BROKEN'
PAYMENT_STATUS_UPDATED = 'PAYMENT_STATUS_UPDATED'
PAYMENT_SERVICE_COULD_NOT_CREATE_ONE_OFF = (
    'PAYMENT_SERVICE_COULD_NOT_CREATE_ONE_OFF')
PAYMENT_SERVICE_COULD_NOT_CREATE_WITH_DEFAULT_PAYMENT_CARD = (
    'PAYMENT_SERVICE_COULD_NOT_CREATE_WITH_DEFAULT_PAYMENT_CARD')
PAYMENT_STATUS_UPDATED = 'PAYMENT_STATUS_UPDATED'
NOT_SUBSCRIPTION_PRODUCT_DETECTED = 'NOT_SUBSCRIPTION_PRODUCT_DETECTED'

# -- Donations
CHECKED_IF_CAN_ATTEMPT_DONATION = 'CHECKED_IF_CAN_ATTEMPT_DONATION'
DONATION_ATTEMPT_CREATED = 'DONATION_ATTEMPT_CREATED'
ANONYMOUS_DONATION_REGISTERED = 'ANONYMOUS_DONATION_REGISTERED'
DONATION_REGISTERED = 'DONATION_REGISTERED'

# -- Created Info
CREATED_PAYMENT = 'CREATED_PAYMENT'

# -- Listed Info

# -- Removed Info
COULD_NOT_REMOVE_DEFAULT_PAYMENT_CARD = 'COULD_NOT_REMOVE_DEFAULT_PAYMENT_CARD'

# -- Subscription
SUBSCRIPTION_PROCESS_INITIATED_REQUEST_PAYMENT_CARD = (
    'SUBSCRIPTION_PROCESS_INITIATED_REQUEST_PAYMENT_CARD')

SUBSCRIPTION_PROCESS_INITIATED_CONFIRM_PAYMENT = (
    'SUBSCRIPTION_PROCESS_INITIATED_CONFIRM_PAYMENT')

SUBSCRIPTION_PROCESS_INITIATED_SHOW_INFO = (
    'SUBSCRIPTION_PROCESS_INITIATED_SHOW_INFO')

ACCOUNT_CONFIRMED_TO_HAVE_REQUESTED_SUBSCRIPTION = (
    'ACCOUNT_CONFIRMED_TO_HAVE_REQUESTED_SUBSCRIPTION')

ACCOUNT_MARKED_FOR_DOWNGRADE = 'ACCOUNT_MARKED_FOR_DOWNGRADE'


class EventFactory:

    def __init__(self, logger):
        self.logger = logger

        # -- warning - no http response
        self.Warning.logger = logger

        # -- 200
        self.Success.logger = logger

        # -- 201
        self.Created.logger = logger

        # -- 400
        self.BrokenRequest.logger = logger

        # -- 404
        self.DoesNotExist.logger = logger

        # -- 401
        self.AuthError.logger = logger

        # -- 403
        self.AccessDenied.logger = logger

        # -- 500
        self.ServerError.logger = logger

    class Context:

        def __init__(self, user_id=None, **kwargs):
            self.user_id = user_id
            self.data = kwargs

    class BaseSuccessException(Exception):

        def __init__(
                self,
                event,
                context=None,
                data=None,
                instance=None):

            context = context or EventFactory.Context()
            self.event = event
            self.data = data or {}
            self.instance = instance

            # -- notify about the event
            message = '{event}: {log_data}'.format(
                event=event,
                log_data=json.dumps({
                    'user_id': getattr(context, 'user_id', 'anonymous'),
                    '@event': event,
                }))
            self.logger.info(message)

    class Success(BaseSuccessException):
        response_class = JsonResponse

    class Created(BaseSuccessException):
        response_class = JsonCreated

    class BaseErrorException(Exception):

        def __init__(
                self,
                event,
                context=None,
                data=None,
                is_critical=False):

            context = context or EventFactory.Context()
            self.event = event
            self.data = data or {}
            self.data.update({
                'user_id': getattr(context, 'user_id', 'anonymous'),
                '@type': 'error',
                '@event': event,
            })
            self.is_critical = is_critical

            # -- notify about the event
            message = '{event}: {data}'.format(
                event=event, data=json.dumps(data))
            if is_critical:
                if isinstance(context, HttpRequest):
                    self.logger.error(
                        message, exc_info=True, extra={'request': context})

                else:
                    self.logger.error(
                        message, exc_info=True, extra={'data': context.data})

            else:
                self.logger.error(message)

    class BrokenRequest(BaseErrorException):
        response_class = JsonBrokenPayload

    class DoesNotExist(BaseErrorException):
        response_class = JsonDoesNotExist

    class ServerError(BaseErrorException):
        response_class = JsonServerError

    class AuthError(BaseErrorException):
        response_class = JsonAuthError

    class AccessDenied(BaseErrorException):
        response_class = JsonAccessDenied

    class Warning(BaseErrorException):
        """
        Is should serve only the logging purposes and therefore should never
        be used for the direct response creation.

        """

        response_class = NotImplementedError
