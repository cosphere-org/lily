# -*- coding: utf-8 -*-

import json

from django.views.generic import View
from django.conf import settings

from base import serializers
from base.command import command
from base.meta import Meta, Domain
from base.access import Access
from base.input import Input
from base.output import Output


class DocsBlueprintView(View):

    class CommandsConfSerializer(serializers.Serializer):
        _type = 'commands_config'

        commands_config = serializers.JSONField()

    @command(
        name='LIST_COMMANDS_CONF_FOR_SERVICE',

        meta=Meta(
            title='Serve commands conf available in the service',
            description='''
                It serves all commands configuration which are exposed in
                the given instance of the service.

            ''',
            domain=Domain(id='internal', name='Internal Management')),

        access=Access(
            access_list=settings.LILY_DOCS_VIEWS_ACCESS_LIST),

        input=Input(with_user=False),

        output=Output(
            serializer=CommandsConfSerializer),
    )
    def get(self, request):

        with open(settings.LILY_DOCS_COMMANDS_CONF_FILE) as conf:
            raise self.event.Success(
                'COMMANDS_CONF_FOR_SERVICE_LISTED',
                instance={'commands_config': json.loads(conf.read())})
