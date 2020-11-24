
from django.urls import re_path

from . import commands


urlpatterns = [

    re_path(
        r'^$',
        commands.EntryPointCommands.as_view(),
        name='entrypoint'),

]
