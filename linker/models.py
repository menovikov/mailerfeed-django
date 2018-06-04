import base64
import hashlib
import requests
from threading import Thread

from django.conf import settings
from django.db import models
from django.core.urlresolvers import reverse
from django.utils import timezone


class Link(models.Model):

	mailing = models.ForeignKey("common.Umailing")
	url_original = models.TextField()
	identifier = models.TextField(null=True, blank=True, unique=True)

	def get_clicks(self, unique=False):
		if unique:
			return LinkClick.objects.filter(link=self, ip__isnull=False,
											city__isnull=False,	lat__isnull=False,
											lon__isnull=False)\
									.order_by()\
									.values_list('http_ua', 'city', 'lat', 'lon')\
									.distinct()
		return LinkClick.objects.filter(link=self, ip__isnull=False,
										city__isnull=False, lat__isnull=False,
										lon__isnull=False)

	def get_short_url(self):
		return settings.DOMAIN + reverse('client_link_click',
										 kwargs={'identifier': self.identifier})

	def save(self, *args, **kwargs):
		super(Link, self).save(*args, **kwargs)
		if not self.identifier:
			self.identifier = hashlib.md5(bytes(self.id)).hexdigest()[:10]
			self.save()


class LinkClick(models.Model):

	link = models.ForeignKey(Link)
	date = models.DateTimeField(auto_now_add=True)
	ip = models.GenericIPAddressField(null=True)
	http_ua = models.TextField(null=True)
	country = models.TextField(null=True, blank=True)
	countryCode = models.CharField(max_length=5, null=True, blank=True)
	region = models.TextField(null=True, blank=True)
	regionName = models.TextField(null=True, blank=True)
	city = models.TextField(null=True, blank=True)
	zip = models.PositiveIntegerField(null=True, blank=True)
	lat = models.FloatField(null=True, blank=True)
	lon = models.FloatField(null=True, blank=True)

	def _discover(self):
		if self.ip:
			r = requests.get(settings.GEO_LINK + self.ip)
			data = r.json()
			if not data.get('status') == 'success':
				return
			self.country = data.get('country')
			self.countryCode = data.get('countryCode')
			self.region = data.get('region')
			self.regionName = data.get('regionName')
			self.city = data.get('city')
			self.zip = data.get('zip')
			self.lat = data.get('lat')
			self.lon = data.get('lon')
			self.save()

	def discover(self):
		t = Thread(target=self._discover)
		t.start()
