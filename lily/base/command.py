# -*- coding: utf-8 -*-

import json
import re
import inspect

from django.conf import settings
from django.db import transaction
from django.db.utils import DatabaseError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

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
                if not is_atomic:
                    return fn(self, request, *args, **kwargs)

                else:
                    success_exception = None
                    with transaction.atomic():
                        try:
                            return fn(self, request, *args, **kwargs)

                        except EventFactory.BaseSuccessException as e:
                            success_exception = e

                    # -- re-raise success exceptions outside of the
                    # -- transaction block in order to make sure that it
                    # -- would not be interpreted by `atomic` block as an
                    # -- error
                    if success_exception:
                        raise success_exception

            except ObjectDoesNotExist as e:
                # -- Rather Hacky way of fetching the name of model
                # -- which raised the DoesNotExist error
                model_name = str(e).split()[0].upper()
                e = event.DoesNotExist(
                    'COULD_NOT_FIND_{}'.format(model_name),
                    context=request,
                    is_critical=True)
                return e.response_class(e.data)

            except MultipleObjectsReturned as e:
                # -- Rather Hacky way of fetching the name of model
                # -- which raised the MultipleObjectsReturned error
                m = re.search(r'than one\s+(?P<model_name>\w+)\s+', str(e))
                model_name = m.group('model_name').upper()

                e = event.ServerError(
                    'FOUND_MULTIPLE_INSTANCES_OF_{}'.format(model_name),
                    context=request,
                    is_critical=True)
                return e.response_class(e.data)

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

            # -- handle gracefully database and generic exceptions
            # -- to make sure that lily valid response will be generated
            except DatabaseError:
                e = event.ServerError(
                    'DATABASE_ERROR_OCCURRED',
                    context=request,
                    is_critical=True)

                return e.response_class(e.data)

            except Exception as err:
                e = event.ServerError(
                    'GENERIC_ERROR_OCCURRED',
                    context=request,
                    data={'errors': [str(err)]},
                    is_critical=True)

                return e.response_class(e.data)

        # -- the below specs are available shortly after the code compilation
        # -- and therefore can be made available on runtime
        code, firstline = inspect.getsourcelines(fn)
        inner.command_conf = {
            'name': name,
            'method': fn.__name__,
            'meta': meta,
            'source': {
                'filepath': inspect.getfile(fn).replace(
                    settings.LILY_PROJECT_BASE, ''),
                'start_line': firstline,
                'end_line': firstline + len(code),
            },
            'path_params_annotations': fn.__annotations__,
            'access_list': access_list,
            'input': input,
            'output': output,
        }

        return inner

    return command_inner
