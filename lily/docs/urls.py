# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views


urlpatterns = [

    url(
        r'^blueprint_spec/$',
        views.BlueprintSpecView.as_view(),
        name='blueprint_spec'),

    url(
        r'^commands/$',
        views.CommandsView.as_view(),
        name='commands'),

]
