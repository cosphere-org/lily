# -*- coding: utf-8 -*-

from .interface import Interface
from .signature import Signature
from .utils import to_camelcase


class Command:

    def __init__(self, name, conf):
        self.name = name
        self.conf = conf

    #
    # GENERAL
    #
    @property
    def method(self):
        return self.conf['method'].lower()

    @property
    def camel_name(self):
        return to_camelcase(self.name)

    #
    # META
    #
    @property
    def domain_id(self):
        return self.conf['meta']['domain']['id']

    @property
    def title(self):
        return self.conf['meta']['title']

    @property
    def description(self):
        return self.conf['meta'].get('description')

    @property
    def header(self):
        if self.description:
            return '''
            /**
             * {self.title}
             * -------------
             *
             * {self.description}
             */
            '''.format(self=self)

        else:
            return '''
            /**
             * {self.title}
             */
            '''.format(self=self)

    #
    # ACCESS
    #
    @property
    def is_private(self):
        return self.conf['access']['is_private']

    #
    # REQUEST / RESPONSE
    #
    @property
    def path(self):
        return self.conf['path_conf']['path']

    @property
    def path_parameters(self):
        return self.conf['path_conf']['parameters']

    @property
    def request_query(self):
        return Interface(self.name, self.conf['schemas']['input_query'])

    @property
    def request_body(self):
        return Interface(self.name, self.conf['schemas']['input_body'])

    @property
    def response(self):
        return Interface(self.name, self.conf['schemas']['output'])

    @property
    def signature(self):
        return Signature(
            self.path,
            self.path_parameters,
            self.request_query,
            self.request_body)
