# -*- coding: utf-8 -*-

import random
from faker import Faker
from lily import Meta, Domain, Access, Source


faker = Faker()


class EntityGenerator:

    def command(self):

        def fn():
            pass

        command = {
            'method': random.choice(['GET', 'POST', 'PUT', 'DELETE']),
            'path_conf': {'path': 'conf'},
            'meta': Meta(
                title=faker.sentence(),
                description=faker.sentence(),
                domain=Domain(id='d', name='domain')),
            'access': Access(
                is_private=random.choice([True, False]),
                access_list=['ANY']),
            'source': Source(fn),
            'schemas': {'some': 'schemas'},
            'examples': {'some': 'examples'},
        }

        return command
