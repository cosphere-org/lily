# -*- coding: utf-8 -*-

from .base import BaseRenderer
from .interface import InterfaceRenderer


class TypeScriptSpecRenderer(BaseRenderer):

    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns

    def render(self):

        base_index = super(TypeScriptSpecRenderer, self).render()
        rendered = {}

        for path, conf in base_index.items():
            for method in ['post', 'get', 'put', 'delete']:
                try:
                    method_conf = conf[method]

                except KeyError:
                    pass

                else:
                    # -- take into account public commands
                    if method_conf['access'].is_private:
                        continue

                    # -- INTERFACES
                    interfaces = {}
                    interfaces['response'] = InterfaceRenderer(
                        method_conf['output'].serializer).render().serialize()

                    if method_conf['input'].query_parser:
                        interfaces['request_query'] = InterfaceRenderer(
                            method_conf['input'].query_parser
                        ).render().serialize()

                    if method_conf['input'].body_parser:
                        interfaces['request_query'] = InterfaceRenderer(
                            method_conf['input'].body_parser
                        ).render().serialize()

                    rendered[method_conf['name']] = {
                        'meta': {
                            'domain': method_conf['meta'].domain.id,
                            'title': method_conf['meta'].title,
                            'description': method_conf['meta'].description,
                        },
                        'method': method,
                        'interfaces': interfaces,
                        # FIXME: add path specification
                        # FIXME: add tests cases for a given command!!!!
                    }

        return rendered

# CLIENT RENDERER
# 1. in the 1st attempt save the repo locally
# 2. produce all interfaces for a list of service-typescript files
# 3. make sure that none command is duplicated
#    (take entity service and fragment service)
# 4. push to github with new tag!!!
# 5. pull from github the template
