
from unittest.mock import Mock

from django.test import TestCase
import pytest

from lily.base.output import Output


class OutputTestCase(TestCase):

    def test_required_fields(self):
        # -- missing serializer
        with pytest.raises(TypeError):
            Output()

    def test_arguments_are_saved(self):
        serializer = Mock()

        o = Output(serializer=serializer)

        assert o.serializer == serializer
