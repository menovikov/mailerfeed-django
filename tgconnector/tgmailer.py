import time
from threading import Thread

from django.conf import settings
from django.dispatch import Signal, receiver
from django.utils import timezone

from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from time import sleep

from common.utils import validate_phone, validate_int
from .models import TGUser, TGMessage, TGMailing, TGSegment


SEND_MAILING_TG = Signal(providing_args=["msg_text", "tg_ids", "profile", "umailing"])
START_SEND_TG = Signal(providing_args=["mailing", "segment"])
TG_SERVICE = [777000,]

def send_code(user, phone):
	print("entered send_code func")
	if not validate_phone(phone):
		return False, 'Error with phone'
	res, error = False, ''
	print("Creating tg client")
	client = TelegramClient(
		user.profile.get_tg_config_loc(),
		settings.TG_CONF['API_ID'],
		settings.TG_CONF['API_HASH'])
	print("Created client")
	connected = client.connect()
	print("Connected ")
	print(connected)
	if connected and client.is_user_authorized() and user.profile.tg_is_connected:
		print("Started contacts loading")
		get_contacts_init(user, client)
		res, error = True, None
	elif connected:
		try:
			sent = client.send_code_request(phone)
			res, error = True, None
			user.profile.tg_phone = phone
			user.profile.tg_phone_code_hash = sent.phone_code_hash
			user.profile.save()
		except Exception as e:
			res, error = False, str(e)
	return res, error or "Error while connecting"

def authorize(req_user, code):
	profile = req_user.profile
	client = TelegramClient(
		profile.get_tg_config_loc(),
		settings.TG_CONF['API_ID'],
		settings.TG_CONF['API_HASH'])
	client._phone_code_hash = profile.tg_phone_code_hash
	try:
		myself = client.sign_in(profile.tg_phone, int(code))
	except Exception as e:
		return False, str(e)
	profile.tg_id = myself.id
	profile.tg_is_connected = True
	profile.tg_username = myself.username
	profile.tg_phone = myself.phone
	profile.tg_name = "%s %s" %(myself.first_name, myself.last_name)
	profile.save()
	get_contacts_init(req_user, client)
	return True, None

def refresh(req_user):
	client = TelegramClient(
		req_user.profile.get_tg_config_loc(),
		settings.TG_CONF['API_ID'],
		settings.TG_CONF['API_HASH'])
	connected = client.connect()
	if connected and client.is_user_authorized():
		get_contacts_init(req_user, client)
		return True, None

	req_user.profile.tg_is_connected = False
	req_user.profile.save()
	return False, "Not authorized"

def refresh_contacts(req_user):
	client = TelegramClient(
		req_user.profile.get_tg_config_loc(),
		settings.TG_CONF['API_ID'],
		settings.TG_CONF['API_HASH'])
	client.connect()
	get_contacts_init(req_user, client)

def get_contacts_init(req_user, client):
	t = Thread(target=get_contacts, args=(req_user, client))
	t.start()

def get_contacts(req_user, client):
	dialogs = []
	users = []
	chats = []

	last_date = None
	chunk_size = 20
	while True:
	    result = client(GetDialogsRequest(
	                 offset_date=last_date,
	                 offset_id=0,
	                 offset_peer=InputPeerEmpty(),
	                 limit=chunk_size
	             ))
	    dialogs.extend(result.dialogs)
	    users.extend(result.users)
	    chats.extend(result.chats)
	    if not result.messages:
	        break
	    last_date = min(msg.date for msg in result.messages)
	    sleep(2)

	for u in users:
		try:
			user = TGUser.objects.get(sid=u.id)
		except TGUser.DoesNotExist:
			user = TGUser()
		if u.is_self:
			continue
		user.sid = u.id
		user.first_name = u.first_name
		user.last_name = u.last_name
		user.username = u.username
		user.phone = u.phone
		user.is_bot = u.bot
		user.is_mutual_contact = u.mutual_contact
		user.is_deleted = u.deleted
		if not user.is_deleted and not user.is_bot and user.sid not in TG_SERVICE:
			user.status = TGUser.ACTIVE
		else:
			user.status = TGUser.INACTIVE
		user.user = req_user
		user.save()

def mailing_send(msg_text, tg_ids, profile, umailing):
	user_ids = [int(x) for x in tg_ids if validate_int(x)]
	users = []
	for id_ in user_ids:
		try:
			users.append(TGUser.objects.get(id=id_))
		except TGUser.DoesNotExist:
			pass
	mailing = TGMailing.objects.create(user=profile.user, content=msg_text,
									   sent=timezone.now())
	umailing.tg_mailing = mailing
	umailing.save()
	segment = TGSegment.objects.create(user=mailing.user, mailing=mailing)
	segment.add_users(users)
	mailing.send()

@receiver(SEND_MAILING_TG)
def mailing_send_init(msg_text, tg_ids, profile, umailing, **kwargs):
	t = Thread(target=mailing_send, args=(msg_text, tg_ids, profile, umailing))
	t.start()

@receiver(START_SEND_TG)
def start_sending(mailing, segment, **kwargs):
	client = TelegramClient(
		mailing.user.profile.get_tg_config_loc(),
		settings.TG_CONF['API_ID'],
		settings.TG_CONF['API_HASH'])
	client.connect()
	sent, failed = 0, 0
	for user in segment.users.all():
		msg = TGMessage.objects.create(user=mailing.user, mailing=mailing,
									   sent=timezone.now(), recipient=user)
		try:
			if not user.phone and user.username:
				raise Exception("No target address")
			t_msg = client.send_message(user.username or user.phone, mailing.content)
			msg.status = TGMessage.SENT
			msg.sid = t_msg.id
			sent += 1
		except Exception as e:
			msg.status = TGMessage.FAILED
			failed += 1
		finally:
			msg.save()
			sleep(2)
	if sent == 0 and failed > 0:
		mailing.status = mailing.FAILED
	elif sent > 0 and failed > 0:
		mailing.status = mailing.PARTIALLY_COMPLETED
	elif sent > 0 and failed == 0:
		mailing.status = mailing.COMPLETED
	mailing.save()

def compare_states(mailing, dialogs=None):
	msgs = TGMessage.objects.filter(mailing=mailing, status__lt=TGMessage.READ,
                                    sid__isnull=False)
	for d in dialogs:
		peer_id = d.peer.chat_id
		if not peer_id:
			continue
		msg = msgs.get(recipient__sid=peer_id)
		if d.read_outbox_max_id >= msg.sid:
			msg.status = TGMessage.READ
			msg.save()
	if TGMessage.objects.filter(mailing=mailing, status__lt=TGMessage.READ,
								sid__isnull=False)\
						.exclude(status_lte=TGMessage.DRAFT).count() == 0:
		mailing.read_state_update = TGMailing.UPDATE_COMPLETED
		mailing.save()
	return

def refresh_read_state(mailing, client):
	dialogs = []
	users = []
	chats = []

	last_date = None
	chunk_size = 20
	while True:
	    result = client(GetDialogsRequest(
	                 offset_date=last_date,
	                 offset_id=0,
	                 offset_peer=InputPeerEmpty(),
	                 limit=chunk_size
	             ))
	    dialogs.extend(result.dialogs)
	    users.extend(result.users)
	    chats.extend(result.chats)
	    if not result.messages:
	        break
	    last_date = min(msg.date for msg in result.messages)
	    sleep(2)
	compare_states(mailing, dialogs=dialogs)

def update_read_state(mailing):
	client = TelegramClient(
		mailing.user.profile.get_tg_config_loc(),
		settings.TG_CONF['API_ID'],
		settings.TG_CONF['API_HASH'])
	connected = client.connect()
	if connected and client.is_user_authorized():
		refresh_read_state(mailing, client)

	req_user.profile.tg_is_connected = False
	req_user.profile.save()
	return
	