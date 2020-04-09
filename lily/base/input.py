
import json

from .events import EventFactory
from ..search import TextVector


class Input(EventFactory):

    class InputAttrs:
        pass

    def __init__(
            self,
            query_parser=None,
            body_parser=None):

        self.query_parser = query_parser
        self.body_parser = body_parser

    def __eq__(self, other):
        return (
            self.query_parser == other.query_parser and
            self.body_parser == other.body_parser)

    def parse(self, request, command_name):
        request.input = self.InputAttrs()

        # -- query parsing
        if self.query_parser:
            request.input.query = self.parse_query(request)

        # -- body parsing
        if self.body_parser:
            request.input.body, request.input.body_raw = self.parse_body(
                request, command_name=command_name)

    def parse_query(self, request):

        parsed = self.query_parser.as_query_parser(data=request.GET)

        if not parsed.is_valid():
            raise self.BrokenRequest(
                'QUERY_DID_NOT_VALIDATE',
                context=request,
                data={'errors': parsed.errors})

        else:
            return parsed.data

    def parse_body(self, request, command_name):
        try:
            body = str(request.body, encoding='utf8') or '{}'
            body = TextVector().transform_special_characters(body)

            data = json.loads(body)

        except (TypeError, ValueError):
            raise self.BrokenRequest(
                'BODY_JSON_DID_NOT_PARSE', context=request, is_critical=True)

        parsed = self.body_parser.as_body_parser(
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
