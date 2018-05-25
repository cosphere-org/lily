# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from ...renderers.angular.renderer import AngularClientRenderer


class Command(BaseCommand):
    help = 'Render Angular Client'

    def handle(self, *args, **options):

        AngularClientRenderer().render()

        self.stdout.write(
            self.style.SUCCESS('Successfully rendered Angular Client'))
