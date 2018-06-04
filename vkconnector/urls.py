from django.conf.urls import url

from .views import (
	vk_auth_redirect,
	vk_user_auth,
	vk_group_auth,
	get_social_communities,
	get_active_subscribers,
	check_user_allowedMessages,
	vk_subscriber_track,
	get_vk_widget,
	vk_logout,
	)


urlpatterns = [
	# url(r'^mailings/new/$', mailing_create, name="mailing_create"),
	# url(r'^message/new/$', message_create, name="message_create"),
	url(r'^communities/get/$', get_social_communities, name="get_social_communities"),
	url(r'^users/get/$', get_active_subscribers, name="get_vk_active_subscribers"),
	url(r'^users/checkallowed/$', check_user_allowedMessages, name="check_user_allowedMessages"),
	url(r'^users/track/$', vk_subscriber_track, name="vk_subscriber_track"),
	# url(r'^users/changeallowed/$', change_user_allowed, name="change_user_allowed"),

	url(r'^auth/redirect/$', vk_auth_redirect, name="vk_auth_redirect"),
	url(r'^auth/user/$', vk_user_auth, name="vk_user_auth"),
	url(r'^auth/group/(?P<group_id>\d+)/$', vk_group_auth, name="vk_group_auth"),

	url(r'^widget/get/$', get_vk_widget, name="get_vk_widget"),
	url(r'^logout/$', vk_logout, name="vk_logout"),
]