# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views


urlpatterns = [

    url(
        r'^blueprint_spec/$',
        views.BlueprintSpecView.as_view(),
        name='blueprint_spec'),

    url(
        r'^typescript_spec/$',
        views.TypeScriptSpecView.as_view(),
        name='typescript_spec'),

]
