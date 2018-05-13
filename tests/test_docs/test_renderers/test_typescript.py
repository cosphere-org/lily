# -*- coding: utf-8 -*-

from unittest import TestCase

import pytest
from mock import Mock

from lily.base import serializers, parsers
from lily.base.input import Input
from lily.base.output import Output
from lily.docs.renderers.typescript import TypescriptInterfaceRenderer
from lily.docs.renderers.base import BaseRenderer


class TypescriptInterfaceRendererTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def test_render(self):

        class TaskParser(parsers.BodyParser):

            name = parsers.CharField()

        class TaskSerializer(serializers.Serializer):

            _type = 'task'

            name = serializers.CharField()

            is_active = serializers.BooleanField()

        self.mocker.patch.object(BaseRenderer, 'render').return_value = {
            '/tasks/': {
                'path_conf': {},
                'post': {
                    'name': 'CREATE_TASK',
                    'meta': {},
                    'input': Input(body_parser=TaskParser),
                    'output': Output(serializer=TaskSerializer),
                },
            }
        }

        assert TypescriptInterfaceRenderer(Mock()).render() is None
