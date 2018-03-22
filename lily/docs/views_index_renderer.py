# -*- coding: utf-8 -*-

from copy import copy
import re

from django.urls import URLResolver, URLPattern


class Renderer:

    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns

    def render(self):
        views_index = self.crawl_views(self.urlpatterns)
        for path, view_conf in views_index.items():
            view = views_index[path]['callback'].view_class

            for method in ['post', 'get', 'put', 'delete']:
                try:
                    view_conf[method] = getattr(view, method).command_conf

                except AttributeError:
                    pass

            del views_index[path]['callback']

        return views_index

    def crawl_views(self, patterns, path_patterns=None):
        views_index = {}

        for pattern in patterns:
            inner_path_patterns = copy(path_patterns)
            if inner_path_patterns:
                inner_path_patterns.append(pattern.pattern.regex.pattern)

            else:
                inner_path_patterns = [pattern.pattern.regex.pattern]

            if isinstance(pattern, URLResolver):
                views_index.update(
                    self.crawl_views(
                        pattern.url_patterns, inner_path_patterns))

            elif isinstance(pattern, URLPattern):
                view_name = pattern.callback.__name__

                ignore_views = [
                    'serve',
                    'add_view',
                    'change_view',
                    'changelist_view',
                    'history_view',
                    'delete_view',
                    'RedirectView',
                ]

                if view_name not in ignore_views:
                    path_conf = self.url_pattern_to_dict(inner_path_patterns)
                    views_index[path_conf['path']] = {
                        'name': view_name,
                        'path_conf': path_conf,
                        'path_patterns': inner_path_patterns,
                        'callback': pattern.callback,
                    }

        return views_index

    def url_pattern_to_dict(self, patterns):
        pattern = ''.join(patterns)

        # -- remove starting `^`
        pattern = re.sub(r'^\^', '/', pattern)
        # -- remove ending `$`
        pattern = re.sub(r'\$$', '', pattern)
        # -- replace middle `/^` with optional `$` (`/$^`)
        pattern = re.sub(r'\/?\$?\^', '/', pattern)
        # -- replace double `//`
        pattern = re.sub(r'\/\/', '/', pattern)

        # -- params
        parameter_types = [
            {'pattern': '\\w+', 'type': 'string'},
            {'pattern': '\\d+', 'type': 'integer'},
        ]

        parameters = []

        while True:
            param_pattern = re.compile(
                r'\(\?P\<(?P<param_name>\w+)\>(?P<param_pattern>[\\dw\+]+)\)')

            match = param_pattern.search(pattern)
            if match:
                span = match.span()
                param_name = match.groupdict()['param_name']
                param_pattern = match.groupdict()['param_pattern']
                param_type = 'string'
                for parameter_type_def in parameter_types:
                    if parameter_type_def['pattern'] == param_pattern:
                        param_type = parameter_type_def['type']
                        break

                pattern = pattern.replace(
                    pattern[span[0]:span[1]],
                    '{{{name}}}'.format(name=param_name))

                parameters.append({
                    'name': param_name,
                    'in': 'path',
                    # FIXME: add description to the parameters
                    'description': '',
                    'required': True,
                    'schema': {
                        'type': param_type
                    }
                })

            else:
                break

        return {
            'path': pattern,
            'parameters': parameters
        }
