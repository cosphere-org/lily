# -*- coding: utf-8 -*-

from django.test import TestCase
from django.db import models
from django_fake_model import models as fake_models
import pytest

from lily.base.models import ImmutableModel


class ImmutableEntity(fake_models.FakeModel, ImmutableModel):

    name = models.CharField(max_length=100)


@ImmutableEntity.fake_me
class ImmutableModelTestCase(TestCase):

    def test_save_not_allowed_for_existing_instance(self):

        e = ImmutableEntity(name='john')
        e.save()

        with pytest.raises(ImmutableModel.ModelIsImmutableError):
            e.name = 'mark'
            e.save()

    def test_create_allowed(self):

        e = ImmutableEntity.objects.create(name='john')

        assert e.name == 'john'
