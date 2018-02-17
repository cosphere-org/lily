
# Lily - microservices by humans for humans

Foundations:
- DDD (Domain Driven Design) = Commands + Events
- TDD+ (Test Driven Development / Documentation)


## Custom Authorizer

Each `command` created in Lily can be protected from viewers who should not be
able to access it. Currently one can pass to the `@command` decorator
`access_list`  which is passed to the `Authorizer` class. By default
the `Authorizer` takes the following form:

```python
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

```

But naturally it can take any form you wish. For example:
- it could expect `Authorization` header and perform `Bearer` token decoding
- it could leverage the existence of `access_list` allowing one to apply some
sophisticated `authorization` policy.

The only thing currently `Authorizer` class **must** provide is the `authorize`
method which adds to the `request` `user_id` and `account_type` attributes.
