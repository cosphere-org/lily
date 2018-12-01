#
# from django.test import TestCase
# from mock import Mock
# import pytest
# import yaml

# from lily.base.meta import Meta, Domain
# from lily.base.output import Output
# from lily.base import serializers
# from lily.docs.renderers import open_api
# from lily.docs.renderers.open_api import OpenApiRenderer
# from lily.docs.renderers.base import BaseRenderer


# class OpenAPIRendererTestCase(TestCase):

#     @pytest.fixture(autouse=True)
#     def initfixture(self, mocker, tmpdir):
#         self.mocker = mocker
#         self.tmpdir = tmpdir

#     def test_render(self):

#         template_file = self.tmpdir.join('open_api_base.yaml')
#         template_content = '''
# openapi: 2.0.1
# info:
#     title: hi there
# paths:
#     {{ paths | safe }}
#         '''
#         template_file.write(template_content)

#         self.mocker.patch.object(
#             open_api, 'BASE_TEMPLATE_PATH', str(template_file))
#         self.mocker.patch.object(BaseRenderer, 'render')
#         self.mocker.patch.object(
#             OpenApiRenderer,
#             'render_paths'
#         ).return_value = {
#             '/test/it': {
#                 'get': {'hello': 'get'},
#                 'post': {
#                     'hello': 'post',
#                     'responses': {
#                         'description': 'hi there',
#                         'content': {
#                             'application/json': {
#                                 'title': 'CrazySerializer',
#                                 'example': {'name': 'George'},
#                             }
#                         }
#                     }
#                 },
#             },
#             '/test/that': {
#                 'delete': {'it is': 'time'}
#             },
#         }

#         rendered = yaml.load(OpenApiRenderer(Mock()).render())
#         assert rendered['openapi'] == '2.0.1'
#         assert rendered['info'] == {'title': 'hi there'}
#         paths = rendered['paths']
#         assert paths['/test/it']['get'] == {'hello': 'get'}
#         assert paths['/test/it']['post'] == {
#             'hello': 'post',
#             'responses': {
#                 'description': 'hi there',
#                 'content': {
#                     'application/json': {
#                         'title': 'CrazySerializer',
#                         'example': {'name': 'George'},
#                     }
#                 }
#             },
#         }
#         assert paths['/test/that']['delete'] == {'it is': 'time'}

#     def test_render_paths(self):
#         class ItemSerializer(serializers.Serializer):
#             name = serializers.CharField()

#         urlpatterns = Mock()
#         self.mocker.patch.object(
#             OpenApiRenderer,
#             'get_examples'
#         ).return_value = {
#             'LIST_ITEMS': {
#                 '502 (SERVER_ERROR)': {
#                     'response': {
#                         'content_type': 'application/json',
#                         'status': 502,
#                         'content': {
#                             'user_id': 434,
#                             '@type': 'error',
#                             '@event': 'SERVER_ERROR',
#                         }
#                     },
#                     'description': 'SERVER_ERROR',
#                     'method': 'get'
#                 },
#             }
#         }
#         views_index = {
#             '/items/': {
#                 'path_conf': {
#                     'path': '/items/',
#                     'parameters': {}
#                 },
#                 'get': {
#                     'name': 'LIST_ITEMS',
#                     'output': Output(
#                         serializer=ItemSerializer),
#                     'meta': Meta(
#                         title='hi there',
#                         description='what?',
#                         domain=Domain(id='d', name='d')),
#                 }
#             }
#         }

#         rendered_paths = OpenApiRenderer(urlpatterns).render_paths(views_index)

#         assert rendered_paths == {
#             '/items/': {
#                 'parameters': {},
#                 'get': {
#                     'operationId': 'LIST_ITEMS',
#                     'description': 'what?',
#                     'summary': 'hi there',
#                     'tags': ['d'],
#                     'responses': {
#                         '502 (SERVER_ERROR)': {
#                             'description': 'SERVER_ERROR',
#                             'content': {
#                                 'application/json': {
#                                     'schema': {
#                                         'title': 'ItemSerializer',
#                                         'example': {
#                                             '@event': 'SERVER_ERROR',
#                                             '@type': 'error',
#                                             'user_id': 434,
#                                         },
#                                         'properties': {
#                                             'name': {
#                                                 'type': 'string'
#                                             }
#                                         },
#                                         'required': ['name'],
#                                         'type': 'object',
#                                     }
#                                 }
#                             },
#                         }
#                     },
#                 },
#             }
#         }
