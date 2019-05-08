
from unittest.mock import Mock

from django.test import TestCase
import pytest

from lily.base.meta import Meta, Domain
from lily.docs.renderers.markdown.renderer import MarkdownRenderer
from lily.entrypoint.base import BaseRenderer
from tests import remove_white_chars


class MarkdownRendererTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def test_render(self):

        self.mocker.patch.object(BaseRenderer, 'render').return_value = {
            'LIST_ITEMS': {
                'path_conf': {
                    'path': '/items/',
                    'parameters': {}
                },
                'method': 'get',
                'meta': Meta(
                    title='hi there',
                    description='what?',
                    domain=Domain(id='d', name='items management')),
            },
            'CREATED': {
                'path_conf': {
                    'path': '/items/',
                    'parameters': {}
                },
                'method': 'post',
                'meta': Meta(
                    title='hi there',
                    description='what?',
                    domain=Domain(id='d', name='items management')),
            },
        }
        self.mocker.patch.object(
            MarkdownRenderer, 'get_examples'
        ).return_value = {
            'CREATED': {
                '201 (CREATED)': {
                    'response': {
                        'content_type': 'application/json',
                        'status': 201,
                        'content': {
                            'user_id': 434,
                            '@event': 'CREATED',
                        }
                    },
                    'request': {
                        'path': 'hello/hi',
                        'headers': {
                            'HI-THERE': 'JSON',
                        },
                        'content': {
                            'hi': 'there'
                        }
                    },
                    'description': 'CREATE',
                    'method': 'post'
                },
            },
            'LIST_ITEMS': {
                '200 (LISTED)': {
                    'response': {
                        'content_type': 'application/json',
                        'status': 200,
                        'content': {
                            'user_id': 434,
                            '@event': 'LISTED',
                        }
                    },
                    'request': {
                        'path': 'wat/178',
                        'headers': {
                            'HI-THERE': 'JSON',
                        }
                    },
                    'description': 'SERVER_ERROR',
                    'method': 'get'
                },
                '502 (SERVER_ERROR)': {
                    'response': {
                        'content_type': 'application/json',
                        'status': 502,
                        'content': {
                            'user_id': 434,
                            '@type': 'error',
                            '@event': 'SERVER_ERROR',
                        }
                    },
                    'request': {
                        'path': 'hello/world',
                        'headers': {
                            'HI-THERE': 'JSON',
                        }
                    },
                    'description': 'SERVER_ERROR',
                    'method': 'get'
                },
            }
        }

        assert remove_white_chars(
            MarkdownRenderer(Mock()).render()
        ) == remove_white_chars('''

            # CoSphere API

            CoSphere's API with hypermedia links

            ## items management

            ### CREATED: POST /items/

            hi there
            what?

            #### 201 (CREATED)

            Request:
            ```http
            POST hello/hi HTTP/1.1
            HI-THERE: JSON
            {
                "hi": "there"
            }
            ```

            Respone:
            ```json
            {
                "@event": "CREATED",
                "user_id": 434
            }
            ```

            ### LIST_ITEMS: GET /items/
            hi there
            what?

            #### 200 (LISTED)

            Request:
            ```http
            GET wat/178 HTTP/1.1
            HI-THERE: JSON
            ```

            Respone:
            ```json
            {
                "@event": "LISTED",
                "user_id": 434
            }
            ```

            #### 502 (SERVER_ERROR)

            Request:
            ```http
            GET hello/world HTTP/1.1
            HI-THERE: JSON
            ```

            Respone:
            ```json
            {
                "@event": "SERVER_ERROR",
                "@type": "error",
                "user_id": 434
            }
            ```

        ''')
