# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views


urlpatterns = [

    url(
        r'^spec/$',
        views.OpenAPISpecView.as_view(),
        name='open_api_spec_view'),

]
