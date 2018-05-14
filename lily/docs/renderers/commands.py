# # -*- coding: utf-8 -*-

# from .schema import to_schema
# from .base import BaseRenderer


# def simplify_json_schema(schema):
#     """
#     Simplify the json schema into easier to consume by humans format.

#     """
#     if not schema:
#         return schema

#     simplified = {}

#     # -- object simplification
#     if schema.get('properties'):
#         simplified['@type'] = 'object'
#         for name, field in schema['properties'].items():
#             # -- field
#             field.get('properties')

#             if field.get('properties'):
#                 simplified[name] = simplify_json_schema(field)

#             else:
#                 simplified[name] = field

#             # -- type
#             simplified[name]['@type'] = field.pop('type')

#             # -- required
#             if name in schema.get('required', []):
#                 simplified[name]['@required'] = True

#     # -- array simplification
#     elif schema.get('items'):
#         simplified['@type'] = 'array'
#         simplified['@items'] = simplify_json_schema(schema['items'])

#     return simplified


# class CommandsRenderer(BaseRenderer):

#     def __init__(self, urlpatterns):
#         self.urlpatterns = urlpatterns

#     def render(self):
#         rendered = {}
#         base_index = super(CommandsRenderer, self).render(self.urlpatterns)
#         for path, conf in base_index.items():
#             for method in ['post', 'get', 'put', 'delete']:
#                 try:
#                     method_conf = conf[method]

#                 except KeyError:
#                     # !!!!!!!!!!!!!!!
#                     # FIXME: ultimately this guy should return error!
#                     # in order to enforce all the views to be in the form
#                     # of commands
#                     pass

#                 else:
#                     command_name = method_conf['name']
#                     rendered[command_name] = {
#                         'method': method,
#                         'access_list': method_conf['access_list'],
#                         # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#                         # FIXME: make it into the real path use env variables
#                         # to achieve that
#                         'service_base_uri': 'http://localhost:8080',
#                         'path_conf': conf['path_conf'],
#                     }

#                     # -- body definition
#                     body_parser = method_conf['input'].body_parser
#                     if body_parser:
#                         rendered[command_name]['body'] = (
#                             simplify_json_schema(to_schema(body_parser)))

#                     # -- query definition
#                     query_parser = method_conf['input'].query_parser
#                     if query_parser:
#                         rendered[command_name]['query'] = (
#                             simplify_json_schema(to_schema(query_parser)))

#         return rendered
