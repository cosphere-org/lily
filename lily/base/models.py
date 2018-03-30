# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.expressions import RawSQL


class ImmutableModel(models.Model):

    class ModelIsImmutableError(Exception):
        pass

    def save(self, *args, **kwargs):

        if self.id is not None:
            raise ImmutableModel.ModelIsImmutableError(
                '{} model is declared as immutable'.format(
                    self.__class__.__name__))

        super(ImmutableModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class ExtraColumn(RawSQL):

    def __init__(self, sql, params, output_field=None):

        super(ExtraColumn, self).__init__(
            sql, params, output_field=output_field)

    def get_group_by_cols(self):
        return []
