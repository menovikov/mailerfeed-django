from django.db import models

from common.models import SocialObject, SocialProfile, SocialCommunity
from common.models import SocialMailing, SocialMessage, SocialSegment


class VKObject(models.Model):
	pass

	def save(self, *args, **kwargs):
		self.network = SocialObject.VK
		super(VKObject, self).save(*args, **kwargs)

	class Meta:
		abstract = True


class VKUser(SocialProfile, VKObject):
	isAllowedMessages = models.BooleanField(default=False)
	group = models.ForeignKey("VKGroup", null=True, blank=True)

	def save(self, refresh=False, *args, **kwargs):
		from .vkmailer import refresh_user
		if refresh:
			refresh_user(self)
		super(VKUser, self).save(*args, **kwargs)


class VKGroup(SocialCommunity, VKObject):
	last_import = models.DateTimeField(null=True, blank=True)

	def get_subscribers(self):
		return VKUser.objects.filter(group=self, isAllowedMessages=True)

	def get_triggers(self):
		from triggers.models import Trigger
		return Trigger.objects.filter(group=self)


class VKMailing(SocialMailing, VKObject):
	group = models.ForeignKey(VKGroup)
	segment = models.ForeignKey("VKSegment")

	def send(self):
		from .vkmailer import START_MAILING_SEND
		self.status = self.IN_PROGRESS
		self.save()
		print("VK received ", self.content)
		# segment = self.get_segment()
		START_MAILING_SEND.send(mailing=self, content=self.content,
								group=self.group, sender=None)


	def get_segment(self):
		return self.segment

	def update_read_state(self):
		from .vkmailer import update_read_state
		update_read_state(self)

	@staticmethod
	def get_mailings(user):
		return VKMailing.objects.filter(user=user)


class VKSegment(SocialSegment, VKObject):
	users = models.ManyToManyField(VKUser)

	def add_users(self, users):
		if users:
			for u in users:
				self.users.add(u)
			self.save()


class VKMessage(SocialMessage, VKObject):
	recipient = models.ForeignKey(VKUser)
	mailing = models.ForeignKey(VKMailing, null=True, blank=True)

	@staticmethod
	def get_messages(user):
		return VKMessage.objects.filter(user=user)
