from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from common.models import SocialObject, UMailing
from vkconnector.models import VKGroup


class Trigger(models.Model):
	"""
	Trigger object, which defines general settings for a trigger without particular
	actions

	"""
	SUBSCRIPTION = 1
	MAILING = 2
	START_CHOICES = (
		(SUBSCRIPTION, 'Подписки'),
		(MAILING, 'Рассылки'),
	)

	DRAFT = 0
	STARTED = 1
	PAUSED = 2
	STOPPED = 3
	STATUS_CHOICES = (
		(DRAFT, "Draft"),
		(STARTED, "Started"),
		(PAUSED, "Paused"),
		(STOPPED, "Stopped"),
	)

	user = models.ForeignKey(User)
	title = models.CharField(max_length=256, default='Unnamed')
	time_from = models.IntegerField(choices=START_CHOICES, default=SUBSCRIPTION)
	status = models.IntegerField(choices=STATUS_CHOICES, default=DRAFT)
	created = models.DateTimeField(auto_now_add=True)

	mailing = models.ForeignKey(UMailing, null=True)
	channel = models.IntegerField(null=True, choices=SocialObject.SOCIAL_NETWORKS)
	group = models.ForeignKey(VKGroup, null=True)

	class Meta:
		ordering = ('-id',)

	def get_status(self):
		return dict(self.STATUS_CHOICES)[self.status]

	def get_actions(self):
		return TriggerChainItem.objects.filter(trigger=self)

	def get_last_action_position(self):
		last = TriggerChainItem.objects.filter(trigger=self).last()
		if last:
			return last.position
		return 0

	def get_target(self):
		if self.channel == SocialObject.VK:
			return "{network} - {group}".format(
				network=dict(SocialObject.SOCIAL_NETWORKS)[self.channel],
				group=self.group.title)
		return dict(SocialObject.SOCIAL_NETWORKS)[self.channel]

	def validate(self):
		if self.channel == SocialObject.VK and not self.group:
			return False, "No vk.com group specified"
		return True, None

	def schedule(self):
		offset = timedelta(seconds=0)
		for act in self.get_actions():
			offset += act.start_after
			act.schedule(countdown=offset.seconds)

	def _set_initial_actions(self):
		TriggerChainItem.objects.create(
			trigger=self, title="Сообщение о рассылке",
			text="Сообщение о том, как отписаться от рассылки")
		TriggerChainItem.objects.create(
			trigger=self, title="Контент",
			text="Некоторый контент")
		TriggerChainItem.objects.create(
			trigger=self, title="Продающее сообщение",
			text="Текст продающего предложения")


@receiver(post_save, sender=Trigger)
def save_mailing(instance, created=None, **kwargs):
	if created and not instance.get_actions():
		instance._set_initial_actions()


class TriggerChainItem(models.Model):
	"""
	Trigger action, which is represented usually by sending a message

	It can be planned, run, deleted, edited.
	"""
	MSG_SEND = 1
	TYPES = (
		(MSG_SEND, "Sending a message"),
	)

	IMMEDIATE = 0
	SECOND = 1
	MINUTE = 60
	HOUR = 3600
	DAY = 86400
	UNITS = (
		(IMMEDIATE, "Сразу"),
		(SECOND, "Секунд"),
		(MINUTE, "Минут"),
		(HOUR, "Часов"),
		(DAY, "Дней"),
	)

	trigger = models.ForeignKey(Trigger)
	position = models.IntegerField()
	title = models.CharField(max_length=256, default='Unnamed')
	text = models.TextField(default='Empty message')
	is_start = models.BooleanField(default=False)
	_start_after = models.DurationField(default=timedelta(hours=1))
	type = models.IntegerField(default=MSG_SEND)

	class Meta:
		unique_together = ("trigger", "position")
		ordering = ("trigger", "position")

	def __str__(self):
		return "Send %s after %s" %(self.text, self.start_after)

	@property
	def start_after(self):
		return self._start_after

	@start_after.setter
	def start_after(self, value):
		if value < 0:
			value = 0
		self._start_after = timedelta(seconds=value)

	def get_start_after(self):
		sec = self.start_after.seconds
		result = (None, "Unnamed", None)
		if sec == self.IMMEDIATE:
			result = (self.IMMEDIATE, dict(self.UNITS)[self.IMMEDIATE], sec)
		elif sec % self.DAY == 0:
			result = (
				self.DAY,
				dict(self.UNITS)[self.DAY],
				sec // self.DAY)
		elif sec % self.HOUR == 0:
			result = (
				self.HOUR,
				dict(self.UNITS)[self.HOUR],
				sec // self.HOUR)
		elif sec % self.MINUTE == 0:
			result = (
				self.MINUTE,
				dict(self.UNITS)[self.MINUTE],
				sec // self.MINUTE)
		elif sec % self.SECOND == 0:
			result = (
				self.SECOND,
				dict(self.UNITS)[self.SECOND],
				sec // self.SECOND)
		return result		

	def save(self, *args, **kwargs):
		self.position = self.trigger.get_last_action_position() + 1
		super(TriggerChainItem, self).save(*args, **kwargs)

	def schedule(self, countdown=10, to=None):
		from triggers.tasks import vk_send_message, send_mailing

		if not self.trigger.time_from == Trigger.MAILING \
		and not self.trigger.mailing \
		and not to:
			raise Exception("Provide to: or change trigger status")

		if self.trigger.time_from == Trigger.SUBSCRIPTION \
		and self.trigger.channel == SocialObject.VK:
			vk_send_message.apply_async(countdown=countdown, kwargs={
				'text': self.text, 'group_id': self.trigger.group.id, 
				'to_id': to.id})
		elif self.trigger.time_from == Trigger.MAILING \
		and self.trigger.mailing:
			kwargs = {
				'channel': self.trigger.channel,
				'text': self.text,
				'mailing_prev_id': self.trigger.mailing.id}
			# send_mailing(**kwargs)
			send_mailing.apply_async(countdown=countdown, kwargs=kwargs)
