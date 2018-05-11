# -*- coding: utf-8 -*-

import json

from django.http.request import HttpRequest
from django.http import JsonResponse


class JsonResponseBase(JsonResponse):

    status_code = NotImplemented

    data = {}

    def __init__(self, data={}):
        super(JsonResponseBase, self).__init__(data=(data or self.data))


class Json200(JsonResponseBase):
    status_code = 200


class Json201(JsonResponseBase):
    status_code = 201


class Json400(JsonResponseBase):
    status_code = 400


class Json401(JsonResponseBase):
    status_code = 401


class Json403(JsonResponseBase):
    status_code = 403


class Json404(JsonResponseBase):
    status_code = 404


class Json409(JsonResponseBase):
    status_code = 409


class Json500(JsonResponseBase):
    status_code = 500


class EventFactory:

    def __init__(self, logger):
        self.logger = logger

        # -- warning - no http response
        self.Warning.logger = logger

        self.Executed.logger = logger

        # -- CRUD
        self.Read.logger = logger
        self.Updated.logger = logger
        self.Deleted.logger = logger
        self.Created.logger = logger

        # -- BULK CRUD
        self.BulkCreated.logger = logger
        self.BulkUpdated.logger = logger
        self.BulkRead.logger = logger
        self.BulkDeleted.logger = logger

        #
        # ERRORS
        #
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

        def __init__(self, user_id=None, email=None, origin=None, **kwargs):
            self.user_id = user_id
            self.email = email
            self.origin = origin

            self.data = {
                'user_id': self.user_id,
                'origin': self.origin,
            }
            self.data.update(kwargs)

        def is_empty(self):
            return not (self.user_id or self.email or self.origin)

        def __eq__(self, other):
            return (
                self.user_id == other.user_id and
                self.email == other.email and
                self.origin == other.origin)

    #
    # SUCCESS RESPONSES
    #
    class BaseSuccessException(Exception):

        verb = None

        def __init__(
                self,
                instance=None,
                data=None,
                event=None,
                context=None):

            self.context = context or EventFactory.Context()
            self.event = event
            self.instance = instance
            self.data = data or {}

        def extend(self, event=None, context=None):
            """
            Sometimes Success Exception is raised without all needed attributes
            since they're unknown at the instantiation time, but are know
            afterwards.

            This method enables one to load required attributes.

            """

            if (self.context and
                    isinstance(self.context, EventFactory.Context) and
                    self.context.is_empty()):
                self.context = context

            if self.event is None:
                self.event = event

            return self

        def log(self):

            user_id = getattr(self.context, 'user_id', None)

            # -- notify about the event
            message = '{event}: {log_data}'.format(
                event=self.event,
                log_data=json.dumps({
                    'user_id': user_id or 'anonymous',
                    '@event': self.event,
                }))
            self.logger.info(message)

    class Executed(BaseSuccessException):
        response_class = Json200

    #
    # CRUD
    #
    class Created(BaseSuccessException):
        response_class = Json201

    class Read(BaseSuccessException):
        response_class = Json200

    class Updated(BaseSuccessException):
        response_class = Json200

    class Deleted(BaseSuccessException):
        response_class = Json200

    #
    # BULK CRUD
    #
    class BulkCreated(BaseSuccessException):

        verb = 'bulk_created'

        response_class = Json201

    class BulkRead(BaseSuccessException):

        verb = 'bulk_read'

        response_class = Json200

    class BulkUpdated(BaseSuccessException):

        verb = 'bulk_updated'

        response_class = Json200

    class BulkDeleted(BaseSuccessException):

        verb = 'bulk_deleted'

        response_class = Json200

    #
    # ERRORS RESPONSES
    #
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

            origin = getattr(context, 'origin', None)
            if origin:
                self.data['@origin'] = origin

            email = getattr(context, 'email', None)
            if email:
                self.data['@email'] = email

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
        response_class = Json400

    class AuthError(BaseErrorException):
        response_class = Json401

    class AccessDenied(BaseErrorException):
        response_class = Json403

    class DoesNotExist(BaseErrorException):
        response_class = Json404

    class Conflict(BaseErrorException):
        response_class = Json409

    class ServerError(BaseErrorException):
        response_class = Json500

    class Warning(BaseErrorException):
        """
        Is should serve only the logging purposes and therefore should never
        be used for the direct response creation.

        """

        response_class = NotImplementedError
