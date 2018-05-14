# -*- coding: utf-8 -*-

import re


class Meta:

    def __init__(self, title, domain, description=None):
        self.title = title
        self.description = self.transform_description(description)
        self.domain = domain

    # FIXME: test it!!!
    def transform_description(self, description):

        if description:
            description = description.strip()
            description = re.sub(r'\n +', ' ', description)

        return description

    def serialize(self):
        return {
            'title': self.title,
            'description': self.description,
            'domain': self.domain.serialize(),
        }


class Domain:

    def __init__(self, id, name):
        self.id = id.lower()
        self.name = name

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
        }

    def __eq__(self, other):
        return (
            self.id == other.id and
            self.name == other.name)
