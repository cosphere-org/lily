# -*- coding: utf-8 -*-


class Access:
    def __init__(self, access_list=None, is_private=False):
        self.is_private = is_private
        self.access_list = access_list

    def serialize(self):
        return {
            'is_private': self.is_private,
            'access_list': self.access_list,
        }

    def __eq__(self, other):
        return (
            self.is_private == other.is_private and
            self.access_list == other.access_list)
