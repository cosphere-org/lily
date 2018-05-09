# -*- coding: utf-8 -*-

import re
import inspect
import logging

from django.conf import settings
from django.db import transaction
from django.db.utils import DatabaseError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from .events import EventFactory
from . import serializers
from .utils import import_from_string
from .access import Access
from .input import Input
from .output import Output
from .name import ConstantName


logger = logging.getLogger()


event = EventFactory(logger)


def command(
        name,
        meta,
        access=None,
        input=None,
        output=None,
        is_atomic=False):

    # -- defaults
    name = (isinstance(name, str) and ConstantName(name)) or name
    access = access or Access(access_list=None)
    input = input or Input()
    output = output or Output(serializer=serializers.EmptySerializer)

    def command_inner(fn):

        def inner(self, request, *args, **kwargs):

            # -- set event factory instance accessible to all view handlers
            self.event = event

            # -- add current command_name for easier reference
            request.command_name = name.render_command_name()

            try:
                #
                # AUTHORIZATION
                #
                if access.access_list:
                    authorizer = import_from_string(
                        settings.LILY_AUTHORIZER_CLASS
                    )(event, access.access_list)
                    authorizer.authorize(request)

                #
                # INPUT
                #
                if input:
                    input.set_event_factory(event).parse(
                        request, command_name=name.render_command_name())

                #
                # IS_ATOMIC
                #
                if not is_atomic:
                    # -- trigger the handler which should raise the success or
                    # -- error response
                    # -- if no exception will be raised we return whatever it
                    # -- was returned since most likely some default Django's
                    # -- mechanism took place
                    return fn(self, request, *args, **kwargs)

                else:
                    success_exception = None
                    with transaction.atomic():
                        try:
                            return fn(self, request, *args, **kwargs)

                        except EventFactory.BaseSuccessException as e:
                            e.extend(
                                context=request,
                                event=name.render_event_name(request, e)).log()

                            success_exception = e

                    # -- re-raise success exceptions outside of the
                    # -- transaction block in order to make sure that it
                    # -- would not be interpreted by `atomic` block as an
                    # -- error
                    if success_exception:
                        raise success_exception

            except EventFactory.BaseSuccessException as e:
                e.extend(
                    context=request,
                    event=name.render_event_name(request, e)).log()

                #
                # OUTPUT
                #
                if e.instance:
                    body = output.serializer(
                        e.instance,
                        context={
                            'request': request,
                            'command_name': name.render_command_name(),
                        }).data

                else:
                    serializer = output.serializer(
                        data=e.data,
                        context={
                            'request': request,
                            'command_name': name.render_command_name(),
                        })

                    #
                    # RESPONSE VALIDATION (Test Server Only)
                    #
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

                if e.event:
                    body['@event'] = e.event

                return e.response_class(body)

            except EventFactory.BaseErrorException as e:
                return e.response_class(e.data)

            #
            # GENERIC ERRORS HANDLING
            #
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
            'name': name.render_command_name(),
            'method': fn.__name__,
            'meta': meta,
            'source': {
                'filepath': inspect.getfile(fn).replace(
                    settings.LILY_PROJECT_BASE, ''),
                'start_line': firstline,
                'end_line': firstline + len(code),
            },
            'path_params_annotations': fn.__annotations__,
            'access': access,
            'input': input,
            'output': output,
        }

        return inner

    return command_inner
