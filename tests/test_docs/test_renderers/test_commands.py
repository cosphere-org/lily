# # -*- coding: utf-8 -*-

# from django.test import TestCase
# import pytest
# from mock import Mock

# from lily.base.command import Input
# from lily.base import parsers
# from lily.docs.renderers.commands import (
#     simplify_json_schema,
#     CommandsRenderer,
# )
# from lily.docs.renderers.base import BaseRenderer


# @pytest.mark.parametrize(
#     'schema, expected',
#     [
#         # -- case 0: empty schema
#         ({}, {}),

#         # -- case 1: simple single field flat schema
#         (
#             {
#                 'properties': {
#                     'external': {'type': 'boolean'},
#                 },
#                 'type': 'object'
#             },
#             {
#                 '@type': 'object',
#                 'external': {
#                     '@type': 'boolean'
#                 }
#             }
#         ),

#         # -- case 2: many fields nested schema
#         (
#             {
#                 'properties': {
#                     'order': {
#                         'properties': {
#                             'merchantPosId': {'type': 'string'},
#                             'status': {'type': 'string'},
#                             'extOrderId': {'type': 'integer'}
#                         },
#                         'required': ['status', 'merchantPosId'],
#                         'type': 'object'
#                     }
#                 },
#                 'required': ['order'],
#                 'type': 'object'
#             },
#             {
#                 '@type': 'object',
#                 'order': {
#                     '@type': 'object',
#                     '@required': True,
#                     'merchantPosId': {
#                         '@type': 'string',
#                         '@required': True,
#                     },
#                     'status': {
#                         '@type': 'string',
#                         '@required': True,
#                     },
#                     'extOrderId': {
#                         '@type': 'integer'
#                     }
#                 }
#             }
#         ),

#         # -- case 3: simple schema with items
#         (
#             {
#                 'items': {
#                     'properties': {
#                         'price': {
#                             'type': 'integer',
#                         },
#                         'amount': {
#                             'type': 'float',
#                         },
#                     },
#                     'required': ['price'],
#                 },
#                 'type': 'array'
#             },
#             {
#                 '@type': 'array',
#                 '@items': {
#                     '@type': 'object',
#                     'price': {
#                         '@type': 'integer',
#                         '@required': True,
#                     },
#                     'amount': {
#                         '@type': 'float',
#                     },
#                 }
#             }
#         ),

#     ])
# def test_simplify_json_schema(schema, expected):

#     assert simplify_json_schema(schema) == expected


# class CommandsConfRendererTestCase(TestCase):

#     @pytest.fixture(autouse=True)
#     def initfixture(self, mocker):
#         self.mocker = mocker

#     def test_render__success__simple_commands(self):

#         urlpatterns = Mock()
#         self.mocker.patch.object(
#             BaseRenderer, 'render'
#         ).return_value = {
#             '/items/{item_id}': {
#                 'path_conf': {'params': []},
#                 'get': {
#                     'name': 'LIST_ITEM',
#                     'access_list': ['LEARNER'],
#                     'input': Input(),
#                 }
#             },
#             '/items/': {
#                 'path_conf': {'params': []},
#                 'post': {
#                     'name': 'CREATE_ITEM',
#                     'access_list': ['MENTOR'],
#                     'input': Input(),
#                 }
#             },
#         }

#         conf = CommandsRenderer(urlpatterns).render()

#         assert conf == {
#             'LIST_ITEM': {
#                 'path_conf': {'params': []},
#                 'access_list': ['LEARNER'],
#                 'method': 'get',
#                 'service_base_uri': 'http://localhost:8080',
#             },
#             'CREATE_ITEM': {
#                 'path_conf': {'params': []},
#                 'access_list': ['MENTOR'],
#                 'method': 'post',
#                 'service_base_uri': 'http://localhost:8080',
#             },
#         }

#     def test_render__success__with_body(self):

#         class ItemParser(parsers.BodyParser):
#             name = parsers.CharField()

#         urlpatterns = Mock()
#         self.mocker.patch.object(
#             BaseRenderer, 'render'
#         ).return_value = {
#             '/items/': {
#                 'path_conf': {'params': []},
#                 'post': {
#                     'name': 'CREATE_ITEM',
#                     'access_list': ['MENTOR'],
#                     'input': Input(body_parser=ItemParser),
#                 },
#             },
#         }

#         conf = CommandsRenderer(urlpatterns).render()

#         assert conf == {
#             'CREATE_ITEM': {
#                 'path_conf': {'params': []},
#                 'access_list': ['MENTOR'],
#                 'method': 'post',
#                 'service_base_uri': 'http://localhost:8080',
#                 'body': {
#                     '@type': 'object',
#                     'name': {
#                         '@type': 'string',
#                         '@required': True,
#                     },
#                 },
#             },
#         }

#     def test_render__success__with_query(self):

#         class FilterParser(parsers.QueryParser):
#             name = parsers.CharField()

#         urlpatterns = Mock()
#         self.mocker.patch.object(
#             BaseRenderer, 'render'
#         ).return_value = {
#             '/items/': {
#                 'path_conf': {'params': []},
#                 'get': {
#                     'name': 'LIST_ITEM',
#                     'access_list': ['MENTOR', 'PARTNER'],
#                     'input': Input(query_parser=FilterParser),
#                 },
#             },
#         }

#         conf = CommandsRenderer(urlpatterns).render()

#         assert conf == {
#             'LIST_ITEM': {
#                 'path_conf': {'params': []},
#                 'access_list': ['MENTOR', 'PARTNER'],
#                 'method': 'get',
#                 'service_base_uri': 'http://localhost:8080',
#                 'query': {
#                     '@type': 'object',
#                     'name': {
#                         '@type': 'string',
#                         '@required': True,
#                     },
#                 },
#             },
#         }
