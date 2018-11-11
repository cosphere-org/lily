
from django.conf.urls import url

from . import views


urlpatterns = [

    url(
        r'^$',
        views.EntryPointView.as_view(),
        name='entrypoint'),

]
