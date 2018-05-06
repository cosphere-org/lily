# -*- coding: utf-8 -*-


class Meta:

    def __init__(self, title, domain, description=None):
        self.title = title
        self.description = description
        self.domain = domain

    def serialize(self):
        return {
            'title': self.title,
            'description': self.description,
            'domain': self.domain.name,
        }


class Domain:

    def __init__(self, id, name):
        self.id = id
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
