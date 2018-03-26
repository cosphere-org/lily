# -*- coding: utf-8 -*-

from django.db import models


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
