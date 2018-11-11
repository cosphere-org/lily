
import os
import re

from .utils import to_camelcase


class Path:

    def __init__(self, base_path):
        self.base_path = base_path

    def join(self, sub_path):
        sub_path = re.sub('^/', '', sub_path)
        return os.path.join(self.base_path, sub_path)


class Domain:

    def __init__(self, domain_id, domain_name):
        self.id = domain_id
        self.name = domain_name
        self.camel_id = to_camelcase(domain_id)

    @property
    def path(self):
        return Path(
            './projects/client/src/domains/{}'.format(self.id))

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id
