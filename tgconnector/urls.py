from django.conf.urls import url

from .views import (
	tg_user_auth,
	tg_check_code,
	get_tg_subs,
	tg_refresh,
	tg_logout,
	)


urlpatterns = [
	# url(r'^vk/auth/redirect/$', vk_auth_redirect, name="vk_auth_redirect"),
	url(r'^auth/user/$', tg_user_auth, name="tg_user_auth"),
	url(r'^auth/user/authorize/$', tg_check_code, name="tg_check_code"),
	url(r'^subs/get/$', get_tg_subs, name="get_tg_subs"),
	url(r'^auth/user/refresh/$', tg_refresh, name="tg_refresh"),
	url(r'^logout/$', tg_logout, name="tg_logout"),
	# url(r'^vk/auth/group/(?P<group_id>\d+)/$', vk_group_auth, name="vk_group_auth"),
]