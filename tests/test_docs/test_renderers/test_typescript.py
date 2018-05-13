# -*- coding: utf-8 -*-

from unittest import TestCase

import pytest
# from mock import Mock

# from lily.base import serializers, parsers
# from lily.docs.renderers.typescript import TypeScriptSpecRenderer
# from lily.docs.renderers.base import BaseRenderer


class TypeScriptSpecRendererTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def test_render(self):
        pass
