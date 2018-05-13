# -*- coding: utf-8 -*-

from .base import BaseRenderer


class TypescriptInterfaceRenderer(BaseRenderer):

    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns

    def render(self):

        base_index = super(TypescriptInterfaceRenderer, self).render()

        for path, conf in base_index.items():
            for method in ['post', 'get', 'put', 'delete']:
                try:
                    method_conf = conf[method]

                except KeyError:
                    pass

                else:
                    method_conf['output'].serializer
                    # method_conf['input']
                    return
