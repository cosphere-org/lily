
import inspect
from uuid import uuid4

from django.http import HttpRequest


# FIXME: test it!!!
class Context:

    def __init__(self, command_name, request):

        # -- to track current command
        self.command_name = command_name

        # -- to track requests send between commands
        if request.META.get('HTTP_X_CS_CORRELATION_ID'):
            self.correlation_id = request.META['HTTP_X_CS_CORRELATION_ID']

        else:
            self.correlation_id = str(uuid4())


# FIXME: test it!!!
def get_context():
    frame = inspect.currentframe()

    while frame:
        request = frame.f_locals.get('request')

        if isinstance(request, HttpRequest):
            return request._lily_context
