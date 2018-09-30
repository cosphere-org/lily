
import re

from django.db import transaction
from django.db.utils import DatabaseError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from lily.conf import settings
from .events import EventFactory
from . import serializers
from .utils import import_from_string
from .access import Access
from .source import Source
from .input import Input
from .output import Output
from .name import ConstantName


event = EventFactory()


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
                    )(access.access_list)
                    authorizer.authorize(request)

                #
                # INPUT
                #
                if input:
                    input.parse(
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

            except EventFactory.Generic as e:
                return e.extend(
                    method=request.method, path=request.path
                ).log().response()

            except EventFactory.BaseSuccessException as e:
                e.extend(
                    context=request,
                    event=name.render_event_name(request, e)).log()

                #
                # RESPONSE VALIDATION (Test Server Only)
                #
                if e.data and request.META.get('SERVER_NAME') == 'testserver':
                    serializer = output.serializer(
                        data=e.data,
                        context={
                            'request': request,
                            'command_name': name.render_command_name(),
                        })

                    if not serializer.is_valid():
                        e = event.BrokenRequest(
                            'RESPONSE_DID_NOT_VALIDATE',
                            context=request,
                            data={'errors': serializer.errors},
                            is_critical=True)

                        return e.response_class(e.data)

                #
                # OUTPUT
                #
                body = output.serializer(
                    e.data or e.instance,
                    context={
                        'request': request,
                        'command_name': name.render_command_name(),
                    }).data

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
                m = re.search(r'than one\s+(?P<model_name>\w+)', str(e))
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
        inner.command_conf = {
            'name': name.render_command_name(),
            'method': fn.__name__,
            'meta': meta,
            'source': Source(fn),
            'access': access,
            'input': input,
            'output': output,
        }

        return inner

    return command_inner
