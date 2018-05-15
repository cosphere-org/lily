# -*- coding: utf-8 -*-

from copy import copy
import logging
import re

from django.urls import URLResolver, URLPattern

from lily.base.events import EventFactory


logger = logging.getLogger()


event = EventFactory(logger)


class BaseRenderer:

    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns

    def render(self):
        views_index = self.crawl_views(self.urlpatterns)
        commands_index = {}

        for path, view_conf in views_index.items():
            view = views_index[path]['callback'].view_class

            for method in ['post', 'get', 'put', 'delete']:
                try:
                    fn = getattr(view, method)

                except AttributeError:
                    pass

                else:
                    try:
                        command_name = fn.command_conf['name']

                    except AttributeError:
                        raise event.BrokenRequest(
                            'NOT_LILY_COMPATIBLE_VIEW_DETECTED',
                            data={
                                'name': views_index[path]['name'],
                            })

                    commands_index[command_name] = {
                        'method': method,
                        'path_conf': views_index[path]['path_conf'],
                    }
                    commands_index[command_name].update(fn.command_conf)

        return commands_index

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
        path = pattern
        while True:
            param_pattern = re.compile(
                r'\(\?P\<(?P<param_name>\w+)\>(?P<param_pattern>[\\dw\+]+)\)')

            match = param_pattern.search(path)
            if match:
                span = match.span()
                param_name = match.groupdict()['param_name']
                param_pattern = match.groupdict()['param_pattern']
                param_type = 'string'
                for parameter_type_def in parameter_types:
                    if parameter_type_def['pattern'] == param_pattern:
                        param_type = parameter_type_def['type']
                        break

                path = path.replace(
                    path[span[0]:span[1]],
                    '{{{name}}}'.format(name=param_name))

                parameters.append({
                    'name': param_name,
                    'type': param_type,
                    # FIXME: add description to the parameters
                    'description': '',
                })

            else:
                break

        return {
            'path': path,
            'pattern': pattern,
            'parameters': parameters
        }
