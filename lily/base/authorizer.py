
from lily.base.events import EventFactory


class AuthorizedResponse:

    def __init__(self, request_access=None, response_headers=None):
        self.request_access = request_access or {}
        self.response_headers = response_headers or {}

    def __eq__(self, other):
        return (
            self.request_access == other.request_access and
            self.response_headers == other.response_headers)


class BaseAuthorizer(EventFactory):
    """Minimal Authorizer Class."""

    def __init__(self, access_list):
        self.access_list = access_list

    def authorize(self, request):
        try:
            return AuthorizedResponse(
                request_access={
                    'account_type': request.META['HTTP_X_ACCOUNT_TYPE'],
                    'user_id': request.META['HTTP_X_USER_ID'],
                })

        except KeyError:
            raise self.AccessDenied('ACCESS_DENIED', context=request)

    def log(self, authorize_data):
        return authorize_data
