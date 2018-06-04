from __future__ import absolute_import, unicode_literals
from . import celery_app as app


@app.task
def vk_send_message(text=None, to_id=None, group_id=None):
	from vkconnector.vkmailer import vk_send_message as send
	from vkconnector.models import VKUser, VKGroup
	
	if not text or not to_id or not group_id:
		raise Exception("Provide required params")
	send(text, user_id=to_id, group_id=group_id)

@app.task
def send_mailing(channel=None, text=None, mailing_prev_id=None):
	from common.models import SocialObject, UMailing

	if not mailing_prev_id or not channel or not text:
		raise Exception("Provide required params")
	mailing = UMailing.objects.get(id=mailing_prev_id)
	mailing.id = None
	mailing.content = text
	mailing.title += " :: sent as trigger action"
	if channel == SocialObject.VK:
		mailing.tg_mailing = None
		social_mailing = mailing.vk_mailing
	elif channel == SocialObject.TG:
		mailing.vk_mailing = None
		social_mailing = mailing.tg_mailing
	segment = social_mailing.get_segment()
	segment_users = segment.users.all()
	social_mailing.id = None
	social_mailing.status = social_mailing.DRAFT
	social_mailing.save()

	segment.id = None
	segment.mailing = social_mailing
	segment.save()
	segment.add_users(segment_users)

	if channel == SocialObject.VK:
		mailing.vk_mailing = social_mailing
	elif channel == SocialObject.TG:
		mailing.tg_mailing = social_mailing

	mailing.save()
	validated = mailing.validate()
	if validated:
		mailing.send(copy=True)
