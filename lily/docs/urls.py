# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views


urlpatterns = [

    url(
        r'^blueprint/$',
        views.DocsBlueprintView.as_view(),
        name='blueprint'),

    # url(
    #     r'^commands_conf/$',
    #     views.DocsCommandConfView.as_view(),
    #     name='command_conf'),

]
