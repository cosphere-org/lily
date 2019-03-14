
import logging
import json

from django.http import JsonResponse, HttpResponse


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


class HttpGenericResponse(HttpResponse):

    def __init__(self, status_code, content, *args, **kwargs):

        self.status_code = status_code
        super(HttpGenericResponse, self).__init__(content, *args, **kwargs)

        self._headers['content-type'] = ('content-type', 'application/json')


class EventFactory:

    def __init__(self):
        self.logger = logging.getLogger()

    class Context:

        # FIXME: maybe think about introducing some extra fields
        # naming into the request overwrite in order to enrich it for
        # errors!!!! --> those fields are added during the authorization
        # phase --> request.authorizer.origin!!!!
        def __init__(self, origin=None, **kwargs):
            self.origin = origin

            self.data = {
                'origin': self.origin,
            }
            self.data.update(kwargs)

        def is_empty(self):
            return not self.origin

        def __eq__(self, other):
            return (
                self.origin == other.origin)

    class Generic(Exception):

        def __init__(self, status_code, content):
            self.status_code = status_code
            self.content = content
            self.logger = logging.getLogger()

        def extend(self, method, path):
            """
            Sometimes Success Exception is raised without all needed attributes
            since they're unknown at the instantiation time, but are know
            afterwards.

            This method enables one to load required attributes.

            """
            self.method = method
            self.path = path

            return self

        def log(self):
            # -- notify about the event
            message = '[{method} {path}] -> {status_code}'.format(
                method=self.method,
                path=self.path,
                status_code=self.status_code)
            self.logger.info(message)

            return self

        def response(self):
            return HttpGenericResponse(self.status_code, self.content)

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
            self.logger = logging.getLogger()

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

            access = getattr(self.context, 'access', {})

            # -- notify about the event
            message = '{event}: {log_data}'.format(
                event=self.event,
                log_data=json.dumps({
                    '@event': self.event,
                    '@access': access,
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

        is_critical = None

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
                '@type': 'error',
                '@event': event,
                '@access': getattr(context, 'access', {}),
            })
            self.logger = logging.getLogger()

            origin = getattr(context, 'origin', None)
            if origin:
                self.data['@origin'] = origin

            self.is_critical = is_critical

            # -- notify about the event
            message = '{event}: {data}'.format(
                event=event, data=json.dumps(data))
            if is_critical or self.is_critical:
                if hasattr(context, 'data'):
                    self.logger.error(
                        message, exc_info=True, extra={'data': context.data})

                else:
                    self.logger.error(
                        message, exc_info=True, extra={'request': context})

            else:
                # -- this will not trigger the sentry notification
                # -- since sentry logger is ignoring log with level below
                # -- ERROR
                self.logger.info(message)

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

        is_critical = True

    class ServerError(BaseErrorException):
        response_class = Json500

        is_critical = True

    class Warning(BaseErrorException):
        """
        Is should serve only the logging purposes and therefore should never
        be used for the direct response creation.

        """

        response_class = NotImplementedError
