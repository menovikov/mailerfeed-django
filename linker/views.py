from django.shortcuts import render, redirect
from django.http import Http404
from ipware.ip import get_ip

from .models import Link, LinkClick


def client_link_click(request, identifier=None):
	if not identifier:
		raise Http404
	ip = get_ip(request)
	try:
		from common.models import Umailing
		mailing = Umailing.objects.get(id=int(identifier.split('-')[0]))
		link = Link.objects.get(mailing=mailing, identifier=identifier)
	except:
		link = Link.objects.get(identifier=identifier)
	click = LinkClick.objects.create(
		link=link, ip=ip,
		http_ua=request.META['HTTP_USER_AGENT'])
	click.discover()
	return redirect(link.url_original)
