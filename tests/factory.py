
import random
from faker import Faker
from lily import Meta, Domain, Access, Source


faker = Faker()


class EntityFactory:

    def command(self, is_private=None, domain_id=None):

        def fn():
            pass

        if is_private is None:
            is_private = random.choice([True, False])

        if domain_id is None:
            domain_id = faker.word()

        command = {
            'method': random.choice(['GET', 'POST', 'PUT', 'DELETE']),
            'path_conf': {'path': 'conf'},
            'meta': Meta(
                title=faker.sentence(),
                description=faker.sentence(),
                domain=Domain(id=domain_id, name='domain')),
            'access': Access(
                is_private=is_private,
                access_list=['ANY']),
            'source': Source(fn),
            'schemas': {'some': 'schemas'},
            'examples': {'some': 'examples'},
        }

        return command
