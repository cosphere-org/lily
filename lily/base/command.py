# -*- coding: utf-8 -*-

import json

from django.conf import settings
from django.db import transaction
from django.db.utils import DatabaseError

from .events import EventFactory
from .utils import import_from_string


class Meta:

    def __init__(self, title, description, tags):
        self.title = title
        self.description = description
        self.tags = tags

    def serialize(self):
        return {
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
        }


class Input:

    class InputAttrs:
        pass

    def __init__(
            self,
            query_parser=None,
            body_parser=None,
            with_user=False):
        self.query_parser = query_parser
        self.with_user = with_user
        self.body_parser = body_parser

    def set_event_factory(self, event_factory):
        self.event = event_factory

        return self

    def parse(self, request, command_name):
        request.input = self.InputAttrs()

        # -- append user - check is such a user exists, otherwise no
        # -- further steps should be evaluated since that would give
        # -- unknown user access to validation rules
        if self.with_user:
            request.input.user = self.get_user(request)

        # -- query parsing
        if self.query_parser:
            request.input.query = self.parse_query(request)

        # -- body parsing
        if self.body_parser:
            request.input.body, request.input.body_raw = self.parse_body(
                request, command_name=command_name)

    def parse_query(self, request):

        parsed = self.query_parser(data=request.GET)

        if not parsed.is_valid():
            raise self.event.BrokenRequest(
                'QUERY_DID_NOT_VALIDATE',
                context=request,
                data={'errors': parsed.errors})

        else:
            return parsed.data

    def parse_body(self, request, command_name):
        try:
            data = json.loads(str(request.body, encoding='utf8'))

        except (TypeError, ValueError):
            raise self.event.BrokenRequest(
                'BODY_JSON_DID_NOT_PARSE', context=request, is_critical=True)

        parsed = self.body_parser(
            data=data,
            context={
                'request': request,
                'command_name': command_name,
            })
        if not parsed.is_valid():
            raise self.event.BrokenRequest(
                'BODY_DID_NOT_VALIDATE',
                context=request,
                data={'errors': parsed.errors})

        else:
            return parsed.data, data

    def get_user(self, request):
        # -- this will only be called in services which are directly
        # -- having access to the User model
        from django.contrib.auth.models import User

        try:
            return User.objects.get(id=request.user_id)

        except User.DoesNotExist:
            raise self.event.AuthError(
                'COULD_NOT_FIND_USER',
                context=request,
                is_critical=True)


class Output:
    def __init__(self, logger, serializer):
        self.logger = logger
        self.serializer = serializer


def command(
        name,
        meta,
        input,
        output,
        is_atomic=False,
        access_list=None):

    def command_inner(fn):

        event = EventFactory(output.logger)

        def inner(self, request, *args, **kwargs):

            if access_list:
                authorizer = import_from_string(
                    settings.LILY_AUTHORIZER_CLASS)(event, access_list)

            # -- add current command_name for easier reference
            request.command_name = name

            try:
                # -- authorization
                if access_list:
                    authorizer.authorize(request)

                # -- input parsing
                if input:
                    input.set_event_factory(event).parse(
                        request, command_name=name)

                # -- trigger the handler which should raise the success or
                # -- error response
                # -- if not exception will be raised we return whatever it
                # -- was returned since most likely some default Django's
                # -- mechanism happened
                return fn(self, request, *args, **kwargs)

            except EventFactory.BaseSuccessException as e:
                # -- serialized output
                if output:
                    # -- for the cases when one returns the instance of
                    # -- model or query set

                    if e.instance:
                        body = output.serializer(
                            e.instance,
                            context={
                                'request': request,
                                'command_name': name,
                            }).data

                    else:
                        serializer = output.serializer(
                            data=e.data,
                            context={
                                'request': request,
                                'command_name': name,
                            })

                        # -- when running tests one can perform full
                        # -- response validation, but in the production
                        # -- it should be omitted
                        if request.META.get('SERVER_NAME') == 'testserver':
                            if serializer.is_valid():
                                body = serializer.data

                            else:
                                e = event.BrokenRequest(
                                    'RESPONSE_DID_NOT_VALIDATE',
                                    context=request,
                                    data={'errors': serializer.errors},
                                    is_critical=True)
                                return e.response_class(e.data)

                        else:
                            body = serializer.initial_data

                else:
                    # -- in cases when one returns bare dictionary for the
                    # -- json serialization
                    body = e.data

                if e.event:
                    body['@event'] = e.event

                response = e.response_class(body)

                return response

            except EventFactory.BaseErrorException as e:
                response = e.response_class(e.data)

                return response

        # -- the below specs are available shortly after the code compilation
        # -- and therefore can be made available on runtime
        inner.command_conf = {
            'name': name,
            'method': fn.__name__,
            'meta': meta,
            'path_params_annotations': fn.__annotations__,
            'access_list': access_list,
            'input': input,
            'output': output,
        }

        def decorated_inner(self, request, *args, **kwargs):
            """
            Since the whole API of Lily is driven by Exceptions we must
            apply the transaction decorator level above the `view` itself
            since otherwise we would not be able to `commit` correctly
            since in Lily even the successful responses are raising
            Exceptions therefore causing the transaction to `rollback`.

            """

            decorated = transaction.atomic(inner)
            try:
                return decorated(self, request, *args, **kwargs)

            except DatabaseError:
                e = event.ServerError(
                    'DATABASE_ERROR_OCCURRED',
                    context=request,
                    is_critical=True)

                return e.response_class(e.data)

            except Exception:
                e = event.ServerError(
                    'GENERIC_ERROR_OCCURRED',
                    context=request,
                    is_critical=True)

                return e.response_class(e.data)

        if is_atomic:
            decorated_inner.command_conf = inner.command_conf
            return decorated_inner

        else:
            return inner

    return command_inner
