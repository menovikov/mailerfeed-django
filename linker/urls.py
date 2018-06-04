from django.conf.urls import url

from .views import (
	client_link_click,
	)

urlpatterns = [
    url(r'^(?P<identifier>\w+)/$', client_link_click, name="client_link_click"),
]