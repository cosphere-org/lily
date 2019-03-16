
from django.conf.urls import url

from . import commands


urlpatterns = [

    url(
        r'^$',
        commands.EntryPointCommands.as_view(),
        name='entrypoint'),

]
