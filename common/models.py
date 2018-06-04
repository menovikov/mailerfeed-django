import os
import re
import hashlib
from itertools import chain
from threading import Thread

from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils import timezone

from notifications.models import BaseNotification


def profile_img_upload_location(profile, filename):
	return "user_profile_img/%s/%s" %(profile.user.username, filename)

class Profile(models.Model):
    """
    Information keeper instance for base User model
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    avatar = models.ImageField(upload_to=profile_img_upload_location, 
                               null=True, blank=True, height_field='height_field', 
                               width_field='width_field')
    height_field = models.IntegerField(default=0, null=True, blank=True)
    width_field = models.IntegerField(default=0, null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True,
                                choices=settings.LANGUAGES, default='ru')
    phone = models.CharField(max_length=25, null=True, blank=True)
    notification_level = models.CharField(max_length=25, choices=BaseNotification.LEVELS,
    									  default=BaseNotification.INFO)

    # VK specific fields
    vk_last_refresh = models.DateTimeField(null=True, blank=True)
    vk_is_connected = models.BooleanField(default=False)
    vk_id = models.PositiveIntegerField(null=True, blank=True)
    vk_avatar = models.TextField(null=True, blank=True)
    vk_name = models.CharField(max_length=256, null=True, blank=True)

    # TG specific fields
    tg_is_connected = models.BooleanField(default=False)
    tg_id = models.PositiveIntegerField(null=True, blank=True)
    tg_last_refresh = models.DateTimeField(null=True, blank=True)
    tg_username = models.CharField(max_length=128, null=True, blank=True)
    tg_name = models.CharField(max_length=256, null=True, blank=True)
    tg_phone = models.CharField(max_length=32, null=True, blank=True)
    tg_phone_code_hash = models.CharField(max_length=256, null=True)

    def get_full_name(self):
    	if not self.first_name and not self.last_name:
    		return "No name"
    	return "%s %s" %(self.first_name, self.last_name)

    def get_phone_number(self):
    	if self.phone:
    		return self.phone
    	else:
    		return "не указан"

    def get_photo_url(self):
    	if self.avatar:
    		return static(self.avatar.url)
    	if self.vk_avatar:
    		return self.vk_avatar
    	return static('default-avatar.png')

    def get_messages(self, count=False):
    	from vkconnector.models import VKMessage
    	from tgconnector.models import TGMessage
    	if count:
    		return VKMessage.objects.filter(user=self.user).count() \
    			 + TGMessage.objects.filter(user=self.user).count()
    	return chain(
    		VKMessage.objects.filter(user=self.user),
    		TGMessage.objects.filter(user=self.user))

    def get_mailings(self):
    	return UMailing.objects.filter(user=self.user)

    def get_segments(self):
    	from vkconnector.models import VKSegment
    	return VKSegment.objects.filter(user=self.user)

    def get_subscribers(self, active=False, inactive=False, count=False, vk=True, tg=True):
        from vkconnector.models import VKUser
        from tgconnector.models import TGUser
        vk_subs, tg_subs = VKUser.objects.none(), TGUser.objects.none()
        if vk:
            vk_subs = VKUser.objects.filter(user=self.user)
            if active and not inactive: 
                vk_subs = vk_subs.filter(status=VKUser.ACTIVE)
            elif inactive and not active:
            	vk_subs = vk_subs.filter(status=VKUser.INACTIVE)
        if tg:
            tg_subs = TGUser.objects.filter(user=self.user)
            if active and not inactive:
                tg_subs = tg_subs.filter(status=TGUser.ACTIVE)
            elif inactive and not active:
            	tg_subs = tg_subs.filter(status=TGUser.INACTIVE)
        if count:
            num = 0
            if vk:
                num += vk_subs.count()
            if tg:
                num += tg_subs.count()
            return num

        subs = []
        if vk:
            subs = chain(subs, vk_subs)
        if tg:
            subs = chain(subs, tg_subs)
        return list(subs)

    def get_triggers(self):
    	from triggers.models import Trigger
    	return Trigger.objects.filter(user=self.user)

    def get_admin_groups(self):
    	from vkconnector.models import VKGroup
    	return VKGroup.objects.filter(user=self.user)

    def get_tg_config_loc(self):
    	return os.path.join(settings.TG_DIR, hashlib.md5(bytes(self.id)).hexdigest())

    def get_conn_count(self):
    	conn = 0
    	if self.vk_is_connected:
    		conn += 1
    	if self.tg_is_connected:
    		conn += 1
    	return conn


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
    	profile = Profile()
    	profile.user = instance
    	profile.first_name = instance.first_name
    	profile.last_name = instance.last_name
    	profile.email = instance.email
    	profile.save()

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
	profile = instance.profile
	changed = []
	if instance.first_name and instance.first_name != profile.first_name:
		profile.first_name = instance.first_name
		changed.append("Имя")
	if instance.last_name and instance.last_name != profile.last_name:
		profile.last_name = instance.last_name
		changed.append("Фамилия")
	if instance.email and instance.email != profile.email:
		profile.email = instance.email
		changed.append("Емейл")
	if not changed:
		return
	from notifications.models import WebNotification
	profile.save()
	notification = WebNotification()
	notification.user = instance
	notification.title = "Изменен профиль: %s в %s" % (
		", ".join(changed), 
		timezone.now().strftime("%d-%m-%Y %H:%M"))
	notification.css_class = BaseNotification.USER_RED
	notification.save()

# Every time django User is deleted,
# registration user is deleted too
@receiver(pre_delete, sender=User)
def delete_registration_user(sender, instance, **kwargs):
    try:
        from registration.models import RegistrationProfile
        RegistrationProfile.objects.get(user=instance).delete()
    except Exception:
        pass


class SocialObject(models.Model):
	'''
	Generic object for social network integration
	'''
	VK = 1
	TG = 2
	FB = 3
	SOCIAL_NETWORKS = (
		(VK, "vk.com"),
		(TG, "telegram.com"),
		# (FB, "facebook.com"),
	)

	user = models.ForeignKey(User, null=True, blank=True)
	network = models.PositiveIntegerField(choices=SOCIAL_NETWORKS)
	created = models.DateTimeField(auto_now=True)

	@staticmethod
	def get_network_title(id):
		try:
			title = dict(SocialObject.SOCIAL_NETWORKS)[id]
		except Exception as e:
			title = "Untitled network"
		finally:
			return title

	def get_network(self):
		return SocialObject.get_network_title(self.network)

	class Meta:
		abstract = True


class SocialProfile(SocialObject):
	'''
	Social network profile, relates to a single user
	'''
	ACTIVE = 1
	UBSUBSCRIBED = 0
	INACTIVE = -1
	STATUSES = (
		(ACTIVE, "Active"),
		(UBSUBSCRIBED, "Unsubscribed"),
		(INACTIVE, "Inactive"),
	)

	sid = models.PositiveIntegerField()
	first_name = models.CharField(max_length=128, null=True, blank=True)
	last_name = models.CharField(max_length=128, null=True, blank=True)
	status = models.IntegerField(choices=STATUSES, default=INACTIVE)

	def get_full_name(self):
		if not (self.first_name or self.last_name) \
		and (getattr(self, 'username') or getattr(self, 'phone')):
			return getattr(self, 'username') or getattr(self, 'phone')
		return "%s %s" %(self.first_name or '', self.last_name or '')

	def get_status(self):
		return dict(self.STATUSES)[self.status]

	def get_link_origin(self):
		if self.network == self.VK:
			return 'https://vk.com/id{id}'.format(id=self.sid)
		elif self.network == self.TG:
			return 'https://web.telegram.org/#/im?p=u{id}'.format(id=self.sid)
		return

	def get_source(self):
		if self.network == SocialObject.VK:
			return self.group.title
		elif self.network == SocialObject.TG:
			return self.user.profile.tg_phone
		return
	
	class Meta:
		abstract = True


class SocialCommunity(SocialObject):
	'''
	Social network community

	Provides ability to store access tokens
	'''
	sid = models.PositiveIntegerField()
	title = models.TextField(null=True, blank=True)
	access_token = models.TextField(null=True, blank=True)
	error_msg = models.TextField(null=True, blank=True)
	
	class Meta:
		abstract = True


class SocialMailing(SocialObject):
	'''
	Mailing for many users at once
	'''
	FAILED = -1
	DRAFT = 0
	IN_PROGRESS = 5
	PARTIALLY_COMPLETED = 8
	COMPLETED = 10
	STATUSES = (
		(FAILED, "Failed"),
		(DRAFT, "Draft"),
		(IN_PROGRESS, "In progress"),
		(PARTIALLY_COMPLETED, "Partially completed"),
		(COMPLETED, "Completed"),
	)

	AWAITING_UPDATE = 1
	UPDATE_COMPLETED = 2
	UPDATE_STATUSES = (
		(AWAITING_UPDATE, "Updating is required"),
		(UPDATE_COMPLETED, "Updating state is completed"),
	)

	status = models.IntegerField(choices=STATUSES, default=DRAFT)
	read_state_update = models.IntegerField(choices=UPDATE_STATUSES, default=AWAITING_UPDATE)
	sent = models.DateTimeField(null=True, blank=True)
	content = models.TextField(default="Empty")

	def get_status(self):
		return dict(self.STATUSES)[self.status]

	def get_msgs_count(self, total=False, sent=False, opened=False):
		msgs = self.get_messages()
		count = msgs.count()
		if total:
			count = msgs.count()
		elif sent:
			count = msgs.filter(status__gte=SocialMessage.SENT).count()
		if opened:
			count = msgs.filter(status=SocialMessage.READ).count()
		return count

	def get_messages(self):
		if self.network == SocialObject.VK:
			from vkconnector.models import VKMessage as Message
		elif self.network == SocialObject.TG:
			from tgconnector.models import TGMessage as Message
		else:
			raise Exception("Wrong network provided")
		return Message.objects.filter(mailing=self)

	@staticmethod
	def get_status_s(s):
		return dict(SocialMailing.STATUSES)[s]

	class Meta:
		abstract = True
		ordering = ('-sent',)


class SocialSegment(SocialObject):
	'''
	Segment for mailings
	'''
	title = models.CharField(max_length=128, null=True)
	
	class Meta:
		abstract = True


class SocialMessage(SocialObject):
	'''
	Single message in social network
	'''

	FAILED = -1
	DRAFT = 0
	SENT = 1
	READ = 2
	STATUSES = (
		(FAILED, "Failed"),
		(DRAFT, "Draft"),
		(SENT, "Sent"),
		(READ, "Read"),
	)

	sid = models.PositiveIntegerField(null=True)
	sent = models.DateTimeField(null=True, blank=True)
	status = models.IntegerField(default=DRAFT)

	class Meta:
		abstract = True

	def get_status(self):
		return dict(self.STATUSES)[self.status]


class UMailing(models.Model):
	'''
	Generic mailing to connect all network-specific mailings
	'''
	user = models.ForeignKey(User)
	title = models.CharField(max_length=256, default="Untitled mailing")
	content = models.TextField(blank=True)
	content_validated = models.TextField(null=True, blank=True)
	vk_mailing = models.OneToOneField("vkconnector.VKMailing", null=True)
	tg_mailing = models.OneToOneField("tgconnector.TGMailing", null=True)
	read_state_update = models.IntegerField(choices=SocialMailing.UPDATE_STATUSES,
											default=SocialMailing.AWAITING_UPDATE)

	class Meta:
		ordering = ('-id',)

	def send(self, vk_group_id=None, tg_ids=None, copy=False):
		from vkconnector.vkmailer import SEND_MAILING_VK
		from tgconnector.tgmailer import SEND_MAILING_TG

		if copy:
			"""
			Copying mailing and segment
			"""
			if self.tg_mailing:
				self.tg_mailing.content = self.content_validated
				self.tg_mailing.save()
				self.tg_mailing.send()
			if self.vk_mailing:
				self.vk_mailing.content = self.content_validated
				self.vk_mailing.save()
				self.vk_mailing.send()
			return

		if vk_group_id:
			SEND_MAILING_VK.send(
				msg_text=self.get_content(),
				group_id=vk_group_id,
				umailing=self,
				sender=None)
		if tg_ids:
			SEND_MAILING_TG.send(
				msg_text=self.get_content(),
				tg_ids=tg_ids,
				umailing=self,
				profile=self.user.profile,
				sender=None)

	def save_as_draft(self, vk_group_id=None, tg_ids=None):
		from vkconnector.vkmailer import save_as_draft_vk
		from tgconnector.tgmailer import save_as_draft_tg

		if vk_group_id:
			save_as_draft_vk(
				msg_text=self.get_content(),
				group_id=vk_group_id,
				umailing=self,
				sender=None)
		if tg_ids:
			save_as_draft_tg(
				msg_text=self.get_content(),
				tg_ids=tg_ids,
				umailing=self,
				profile=self.user.profile,
				sender=None)


	def get_content(self):
		return self.content_validated or self.content

	def get_status(self):
		statuses = []
		if self.vk_mailing:
			statuses.append(self.vk_mailing.status)
		if self.tg_mailing:
			statuses.append(self.tg_mailing.status)
		if set(statuses) == set([SocialMailing.FAILED, SocialMailing.COMPLETED]):
			status = SocialMailing.PARTIALLY_COMPLETED
		elif statuses:
			status = min(statuses)
		else:
			status = SocialMailing.DRAFT
		return SocialMailing.get_status_s(status)

	def created(self):
		dates = []
		if self.vk_mailing:
			dates.append(self.vk_mailing.created)
		if self.tg_mailing:
			dates.append(self.tg_mailing.created)
		if dates:
			return min(dates)
		return

	def validate(self):
		from linker.models import Link
		if self.content == '':
			self.content = "Empty message"
		if not self.content:
			return False
		urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', self.content)
		content_validated = self.content
		if urls:
			for url in urls:
				link = Link.objects.create(mailing=self, url_original=url)
				content_validated = content_validated.replace(url, link.get_short_url())
		self.content_validated = content_validated
		self.save()
		return True

	def get_msgs_count(self, total=False, sent=False, opened=False):
		count = 0
		if self.vk_mailing:
			count += self.vk_mailing.get_msgs_count(total=total, sent=sent,
													opened=opened)
		if self.tg_mailing:
			count += self.tg_mailing.get_msgs_count(total=total, sent=sent,
													opened=opened)
		return count

	def get_networks(self):
		networks = []
		if self.vk_mailing:
			networks.append("vk.com")
		if self.tg_mailing:
			networks.append("telegram")
		return ", ".join(networks)

	def get_recipients(self):
		vk_res, tg_res = [], []
		if self.vk_mailing:
			try:
				vk_res = self.vk_mailing.get_segment().users.all()
			except:
				pass
		if self.tg_mailing:
			try:
				tg_res = self.tg_mailing.get_segment().users.all()
			except:
				pass
		return chain(vk_res, tg_res)

	def get_messages(self):
		vk_msgs, tg_msgs = [], []
		if self.vk_mailing:
			vk_msgs = self.vk_mailing.get_messages()
		if self.tg_mailing:
			tg_msgs = self.tg_mailing.get_messages()
		return chain(vk_msgs, tg_msgs)

	def get_links(self):
		from linker.models import Link
		return Link.objects.filter(mailing=self)

	def update_read_state(self):
		'''
		Each mailing is going to be updated only in case it has status AWAITING_UPDATE
		'''
		threads = []
		if self.vk_mailing and self.vk_mailing.read_state_update != SocialMailing.UPDATE_COMPLETED:
			threads.append(Thread(target=self.vk_mailing.update_read_state))
		# if self.tg_mailing and self.tg_mailing.read_state_update != SocialMailing.UPDATE_COMPLETED:
		# 	threads.append(Thread(target=self.tg_mailing.update_read_state))
		if threads:
			for t in threads:
				t.start()
			for t in threads:
				t.join()
		return


@receiver(post_save)
def save_mailing(instance, created=None, **kwargs):
	if issubclass(instance.__class__, UMailing) and created:
		from notifications.models import WebNotification
		notification = WebNotification()
		notification.user = instance.user
		notification.title = "Отправлена рассылка %s в %s" \
			% (instance.get_networks(), timezone.now().strftime("%d-%m-%Y %H:%M"))
		notification.css_class = BaseNotification.USERS_BLUE
		notification.save()
