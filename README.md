
# WARNING: this project is still undergoing some heavy changes and is still quite poorly documented so if you're interested in using it, well do that at your own risk.

# Lily - microservices by humans for humans

Lily is built around:
- DDD (Domain Driven Design) = Commands + Events
- TDD+ (Test Driven Development / Documentation)

## Foundations

Lily was inspired by various existing tools and methodologies. In order to understand the philosophy of `Lily` one must udnerstand two basic concepts:
- `COMMAND` - is a thing one can perform
- `EVENT` - is a consequence of executing `COMMAND` (one `COMMAND` can lead to many events).

In `lily` we define commands that are raising (python's `raise`) various events that are captured by the main events loop (do not confuse with node.js event loop).

## Prerequisites

It is assumed that each `lily` project was setup together with the [`lily-assistant` tool](https://github.com/cosphere-org/lily-assistant) and that `lily_assistant init <src_dir_name>` command was executed therefore:

- `.lily` folder exists in the root directory of the project
- `.lily/config.json` was defined.


## Creating HTTP commands

`Lily` enable very simple and semantic creation of commands using various transport mechanism (HTTP, Websockets, Async) in a one unified way.

Each HTTP command is build around the same skeleton:

```python
from lily import (
    command,
    Meta,
    name,
    Input,
    Output,
    serializers,
    Access,
    HTTPCommands,
)

class SampleCommands(HTTPCommands):
    @command(
        name=<NAME>,

        meta=Meta(
            title=<META_TITLE>,
            description=<META_DESCRIPTION>,
            domain=<META_DOMAIN>),

        access=Access(access_list=<ACCESS_LIST>),

        input=Input(body_parser=<BODY_PARSER>),

        output=Output(serializer=<SERIALIZER>),
    )
    def <HTTP_VERB>(self, request):

        raise self.event.<EXPECTED_EVENT>({'some': 'thing'})
```



The simplest are HTTP commands that can be defined in the following way:

```python
from lily import (
    command,
    Meta,
    name,
    Input,
    Output,
    serializers,
    Access,
    HTTPCommands,
)

class SampleCommands(HTTPCommands):
    @command(
        name=name.Read(CatalogueItem),

        meta=Meta(
            title='Bulk Read Catalogue Items',
            domain=CATALOGUE),

        access=Access(access_list=['ADMIN']),

        input=Input(body_parser=CatalogueItemParser),

        output=Output(serializer=serializers.EmptySerializer),
    )
    def get(self, request):

        raise self.event.Read({'some': 'thing'})
```


### Names
FIXME: add it ...

## Creating Authorizer class

Each `command` created in Lily can be protected from viewers who should not be
able to access it. Currently one can pass to the `@command` decorator
`access_list`  which is passed to the `Authorizer` class.

```python
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

```

But naturally it can take any form you wish. For example:
- it could expect `Authorization` header and perform `Bearer` token decoding
- it could leverage the existence of `access_list` allowing one to apply some
sophisticated `authorization` policy.

An example of fairly classical (jwt token based `Authorizer` would be):


```python
from lily import BaseAuthorizer
from .token import AuthToken


class Authorizer(BaseAuthorizer):

    def __init__(self, access_list):
        self.access_list = access_list

    def authorize(self, request):

        try:
            type_, token = request.META['HTTP_AUTHORIZATION'].split()

        except KeyError:
            raise self.AuthError('COULD_NOT_FIND_AUTH_TOKEN')

        else:
            if type_.lower().strip() != 'bearer':
                raise self.AuthError('COULD_NOT_FIND_AUTH_TOKEN')

        account = AuthToken.decode(token)

        if account.type not in self.access_list:
            raise self.AccessDenied('ACCESS_DENIED')

        # -- return the enrichment that should be available as
        # -- `request.access` attribute
        return {'account': account}

    def log(self, authorize_data):
        return {
            'account_id': authorize_data['account'].id
        }

```

Notice how above custom `Authorizer` class inherits from `BaseAuthorizer`.
In order to enable custom `Authorizer` class one must set in the `settings.py`:

```python
LILY_AUTHORIZER_CLASS = 'account.authorizer.Authorizer'
```

where naturally the module path would depend on a specific project set up.

Finally in order to use Authorization at the command level one must set in the @command definition:

```python
from lily import (
    command,
    Meta,
    name,
    Output,
    serializers,
    Access,
    HTTPCommands,
)

class SampleCommands(HTTPCommands):
    @command(
        name=name.Read(CatalogueItem),

        meta=Meta(
            title='Bulk Read Catalogue Items',
            domain=CATALOGUE),

        access=Access(access_list=['ADMIN']),

        output=Output(serializer=serializers.EmptySerializer),
    )
    def get(self, request):

        raise self.event.Read({'some': 'thing'})
```

where `access` entry explicitly specifies who can access a particular command, that list will be injected to the `Authorizer` on each request to the server.

## Rendering Commands (entrypoint)

By calling:

```bash
make docs_render_markdown
```

One will render `.lily/API.md` file which will contain the Markdown version of the commands specification.

## Rendering API.md

By calling:

```bash
make docs_render_commands
```

One will render `.lily/commands/<version>.json` file which will contain the JSON version of the commands specification for a current version of the service. (this could be used for the automatic detection of Changelog).


## Managing the state of database

Lily exposes three commands for managing migrations:

```bash
make migrations_create
make migrations_bulk_read
make migrations_apply
```

Which are just a wrappers around the commands exposed by django's built-in migration tool.

## Full text search support
FIXME: add it ...

