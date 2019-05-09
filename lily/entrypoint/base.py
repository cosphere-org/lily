
from copy import copy, deepcopy
import re

from django.urls import URLResolver, URLPattern

from lily.base.events import EventFactory


class BaseRenderer(EventFactory):

    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns

    def render(self):
        views_index = self.crawl_views(self.urlpatterns)

        self.validate_index(views_index)

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
                        raise self.BrokenRequest(
                            'NOT_LILY_COMPATIBLE_VIEW_DETECTED',
                            data={
                                'name': views_index[path]['name'],
                            })

                    if command_name in commands_index:
                        existing = commands_index[command_name]

                        raise self.BrokenRequest(
                            'DUPLICATED_COMMAND_DETECTED',
                            data={
                                'command_name': command_name,
                                'existing_command': {
                                    'path': existing['path_conf']['path'],
                                    'method': existing['method'].upper(),
                                },
                                'duplicate_command': {
                                    'path': path,
                                    'method': method.upper(),
                                },
                            })

                    commands_index[command_name] = {
                        'method': method.upper(),
                        'path_conf': deepcopy(views_index[path]['path_conf']),
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
                r'\(\?P\<(?P<param_name>\w+)\>(?P<param_pattern>[^\)]+)\)')

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

    def validate_index(self, views_index):

        view_paths_count = {}
        for view_conf in views_index.values():
            view_name = view_conf['callback'].view_class.__name__

            view_paths_count.setdefault(view_name, 0)
            view_paths_count[view_name] += 1

        duplicates = [
            view_name
            for view_name, view_path_count in view_paths_count.items()
            if view_path_count > 1]

        if duplicates:
            raise self.ServerError(
                'VIEWS_BELONGING_TO_MULTIPLE_PATHS_DETECTED',
                data={'duplicates': duplicates})
