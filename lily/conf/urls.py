# -*- coding: utf-8 -*-

from django.conf.urls import url, include

urlpatterns = [

    url(
        r'^/$',
        include(('entrypoint.urls', 'entrypoint'), namespace='entrypoint')),

    url(
        r'^docs/$',
        include(('docs.urls', 'docs'), namespace='docs')),

]
