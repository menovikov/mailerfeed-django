from django.db import models

from common.models import SocialObject, SocialProfile
from common.models import SocialMailing, SocialMessage, SocialSegment


class TGObject(models.Model):
	pass

	def save(self, *args, **kwargs):
		self.network = SocialObject.TG
		super(TGObject, self).save(*args, **kwargs)

	class Meta:
		abstract = True


class TGUser(SocialProfile, TGObject):
	is_bot = models.BooleanField(default=False)
	is_contact = models.BooleanField(default=False)
	is_deleted = models.BooleanField(default=False)
	is_self = models.BooleanField(default=False)
	is_mutual_contact = models.BooleanField(default=False)
	is_restricted = models.BooleanField(default=False)
	username = models.CharField(max_length=128, null=True)
	phone = models.CharField(max_length=64, null=True)


class TGMailing(SocialMailing, TGObject):

	def send(self, client=None):
		from .tgmailer import START_SEND_TG
		self.status = self.IN_PROGRESS
		self.save()
		segment = self.get_segment()
		START_SEND_TG.send(mailing=self, segment=segment, sender=None)

	def get_segment(self):
		return TGSegment.objects.filter(mailing=self).first()

	def update_read_state(self):
		pass


class TGSegment(SocialSegment, TGObject):
	users = models.ManyToManyField(TGUser)
	mailing = models.ForeignKey(TGMailing)

	def add_users(self, users):
		if users:
			for u in users:
				self.users.add(u)
			self.save()


class TGMessage(SocialMessage, TGObject):
	recipient = models.ForeignKey(TGUser)
	mailing = models.ForeignKey(TGMailing, null=True, blank=True)
