# -*- coding: utf-8 -*-


class Authorizer:
    """
    Minimal Authorizer Class.

    """

    def __init__(self, event, access_list):
        self.event = event
        self.access_list = access_list

    def authorize(self, request):
        try:
            request.user_id = request.META['HTTP_X_CS_USER_ID']
            request.account_type = request.META['HTTP_X_CS_ACCOUNT_TYPE']

        except KeyError:
            raise self.event.AccessDenied('ACCESS_DENIED', context=request)
