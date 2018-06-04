from django.conf.urls import url

from .views import (
	triggers,
	triggers_detail,
	triggers_setstatus,
	triggers_delete,
    get_mailings,
	)

urlpatterns = [
    url(r'^new/$', triggers_detail, name="triggers_new"),
    url(r'^mailings/get/$', get_mailings, name="get_mailings"),
    url(r'^(?P<id>\d+)/$', triggers_detail, name="triggers_detail"),
    url(r'^(?P<id>\d+)/status/(?P<status>\d+)/$', triggers_setstatus,
    	name="triggers_setstatus"),
    url(r'^(?P<id>\d+)/delete/$', triggers_delete, name="triggers_delete"),
    url('', triggers, name="triggers"),
]