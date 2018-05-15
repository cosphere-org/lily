# -*- coding: utf-8 -*-

import inspect

from django.conf import settings

from . import serializers


class Source:

    def __init__(self, fn):
        code, firstline = inspect.getsourcelines(fn)
        self.filepath = inspect.getfile(fn).replace(
            settings.LILY_PROJECT_BASE, '')
        self.start_line = firstline
        self.end_line = firstline + len(code) - 1


class SourceSerializer(serializers.Serializer):

    _type = 'source'

    filepath = serializers.CharField()

    start_line = serializers.IntegerField()

    end_line = serializers.IntegerField()
