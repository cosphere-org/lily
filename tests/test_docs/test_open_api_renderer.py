# -*- coding: utf-8 -*-

from django.test import TestCase
from mock import Mock
import pytest
import yaml

from lily.base.command import Meta, Output
from lily.base import serializers
from lily.docs.open_api_renderer import Renderer, ViewsIndexRender


class OpenAPIRenderer(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def test_render(self):

        template_file = self.tmpdir.join('open_api_spec_base.yaml')
        template_content = '''
openapi: 2.0.1
info:
    title: hi there
paths:
    {{ paths | safe }}
        '''
        template_file.write(template_content)

        self.mocker.patch(
            'docs.open_api_renderer.BASE_TEMPLATE_PATH', str(template_file))
        self.mocker.patch.object(ViewsIndexRender, 'render')
        self.mocker.patch.object(Renderer, 'render_paths').return_value = {
            '/test/it': {
                'get': {'hello': 'get'},
                'post': {
                    'hello': 'post',
                    'responses': {
                        'description': 'hi there',
                        'content': {
                            'application/json': {
                                'title': 'CrazySerializer',
                                'example': {'name': 'George'},
                            }
                        }
                    }
                },
            },
            '/test/that': {
                'delete': {'it is': 'time'}
            },
        }

        rendered = yaml.load(Renderer(Mock()).render())
        assert rendered['openapi'] == '2.0.1'
        assert rendered['info'] == {'title': 'hi there'}
        paths = rendered['paths']
        assert paths['/test/it']['get'] == {'hello': 'get'}
        assert paths['/test/it']['post'] == {
            'hello': 'post',
            'responses': {
                'description': 'hi there',
                'content': {
                    'application/json': {
                        'title': 'CrazySerializer',
                        'example': {'name': 'George'},
                    }
                }
            },
        }
        assert paths['/test/that']['delete'] == {'it is': 'time'}

    def test_render_paths(self):
        class ItemSerializer(serializers.Serializer):
            name = serializers.CharField()

        urlpatterns = Mock()
        self.mocker.patch.object(Renderer, 'get_examples').return_value = {
            'LIST_ITEMS': {
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
                    'description': 'SERVER_ERROR',
                    'method': 'get'
                },
            }
        }
        views_index = {
            '/items/': {
                'path_conf': {
                    'path': '/items/',
                    'parameters': {}
                },
                'get': {
                    'name': 'LIST_ITEMS',
                    'output': Output(
                        logger=Mock(),
                        serializer=ItemSerializer),
                    'meta': Meta(
                        title='hi there',
                        description='what?',
                        tags=['tag_it']),
                }
            }
        }

        rendered_paths = Renderer(urlpatterns).render_paths(views_index)

        assert rendered_paths == {
            '/items/': {
                'parameters': {},
                'get': {
                    'operationId': 'LIST_ITEMS',
                    'description': 'what?',
                    'summary': 'hi there',
                    'tags': ['tag_it'],
                    'responses': {
                        '502 (SERVER_ERROR)': {
                            'description': 'SERVER_ERROR',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'title': 'ItemSerializer',
                                        'example': {
                                            '@event': 'SERVER_ERROR',
                                            '@type': 'error',
                                            'user_id': 434,
                                        },
                                        'properties': {
                                            'name': {
                                                'type': 'string'
                                            }
                                        },
                                        'required': ['name'],
                                        'type': 'object',
                                    }
                                }
                            },
                        }
                    },
                },
            }
        }
