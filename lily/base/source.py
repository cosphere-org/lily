# -*- coding: utf-8 -*-

import inspect

from lily.conf import settings
from . import serializers


class Source:

    def __init__(self, fn):
        code, firstline = inspect.getsourcelines(fn)
        self.filepath = inspect.getfile(fn).replace(
            settings.LILY_PROJECT_BASE, '')
        self.start_line = firstline
        self.end_line = firstline + len(code) - 1

    def __eq__(self, other):
        return (
            self.filepath == other.filepath and
            self.start_line == other.start_line and
            self.end_line == other.end_line)


class SourceSerializer(serializers.Serializer):

    _type = 'source'

    filepath = serializers.CharField()

    start_line = serializers.IntegerField()

    end_line = serializers.IntegerField()
