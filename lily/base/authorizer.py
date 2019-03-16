
from lily.base.events import EventFactory


class BaseAuthorizer(EventFactory):
    """Minimal Authorizer Class."""

    def __init__(self, access_list):
        self.access_list = access_list

    def authorize(self, request):
        try:
            return {
                'user_id': request.META['HTTP_X_CS_USER_ID'],
                'account_type': request.META['HTTP_X_CS_ACCOUNT_TYPE'],
            }

        except KeyError:
            raise self.AccessDenied('ACCESS_DENIED', context=request)

    def log(self, authorize_data):
        return authorize_data
