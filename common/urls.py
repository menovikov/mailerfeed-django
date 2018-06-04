from django.conf.urls import url

from .views import (
	dashboard,
	social_networks,
	redirect_url,
	mailings,
	mailings_detail,
	subscribers,
	subscribers_growth,
	profile,
	send_mailing,
	save_draft_mailing,
	mailings_detail_stat,
	mailings_detail_clicks_stat,
	segments,
	segments_detail,
	)

urlpatterns = [
    url(r'^dashboard/$', dashboard, name="dashboard"),
    url(r'^networks/$', social_networks, name="networks"),
    url(r'^mailings/$', mailings, name="mailings"),
    url(r'^mailings/(?P<id>\d+)/$', mailings_detail, name="mailings_detail"),
    url(r'^mailings/stat/openings/$', mailings_detail_stat, name="mailings_detail_stat"),
    url(r'^mailings/stat/clicks/$', mailings_detail_clicks_stat, name="mailings_detail_clicks_stat"),
    url(r'^segments/$', segments, name="segments"),
    url(r'^segments/detail/$', segments_detail, name="segments_detail"),
    url(r'^subscribers/$', subscribers, name="subscribers"),
    url(r'^subscribers/growth/$', subscribers_growth, name="subscribers_growth"),
    url(r'^profile/$', profile, name="profile"),
    url(r'^mailing/send/$', send_mailing, name="send_mailing"),
    url(r'^mailing/save/$', save_draft_mailing, name="save_draft_mailing"),
    url('', redirect_url, name="redirect_url"),
]