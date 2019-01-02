
import json

from .events import EventFactory


class Input(EventFactory):

    class InputAttrs:
        pass

    def __init__(
            self,
            query_parser=None,
            body_parser=None,
            header_parser=None,
            with_user=False):
        self.query_parser = query_parser
        self.with_user = with_user
        self.body_parser = body_parser

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

        return self._use_parser(request, self.query_parser)

    def _use_parser(self, request, parser):
        parsed = parser(data=request.GET)

        if not parsed.is_valid():
            raise self.BrokenRequest(
                'QUERY_DID_NOT_VALIDATE',
                context=request,
                data={'errors': parsed.errors})

        else:
            return parsed.data

    def parse_body(self, request, command_name):
        try:
            data = json.loads(str(request.body, encoding='utf8'))

        except (TypeError, ValueError):
            raise self.BrokenRequest(
                'BODY_JSON_DID_NOT_PARSE', context=request, is_critical=True)

        parsed = self.body_parser(
            data=data,
            context={
                'request': request,
                'command_name': command_name,
            })
        if not parsed.is_valid():
            raise self.BrokenRequest(
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
            raise self.AuthError(
                'COULD_NOT_FIND_USER',
                context=request,
                is_critical=True)
