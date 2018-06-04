import time
from threading import Thread

from django.dispatch import Signal, receiver
from django.conf import settings
from django.utils import timezone
import vk_api
from vk_api.exceptions import ApiError

from .models import VKGroup, VKUser, VKMessage, VKMailing, VKSegment

GET_GROUPS = Signal(providing_args=["access_token", "user"])
AUTHORIZE_GROUP = Signal(providing_args=["access_token", "group_id", "user"])
SEND_MAILING_VK = Signal(providing_args=["msg_text", "group_id", "umailing"])
START_MAILING_SEND = Signal(providing_args=["group", "content", "segment"])
UPDATE_READ_STATE = Signal(providing_args=["mailing"])


def captcha_handler(self, captcha):
    key = None
    return captcha.try_again(key)

def api_init(group, access_token=None):
    session = vk_api.VkApi(
        token=access_token or group.access_token,
        app_id=settings.VK_CONF['APP_ID'],
        scope='offline', captcha_handler=captcha_handler)
    session.auth()
    api = session.get_api()
    return api

def refresh_user(vk_user):
    api = api_init(vk_user.group)
    user_info = api.users.get(user_id=vk_user.sid)[0]
    vk_user.first_name = user_info.get('first_name')
    vk_user.last_name = user_info.get('last_name')


@receiver(GET_GROUPS)
def get_groups(access_token, user, **kwargs):
    session = vk_api.VkApi(token=access_token, app_id=settings.VK_CONF['APP_ID'],
                           scope='offline', captcha_handler=captcha_handler)
    session.auth()
    api = session.get_api()
    groups = api.groups.get(extended=True, filter='admin')['items']
    for group in groups:
        try:
            g = VKGroup.objects.get(sid=group.get('id'), user=user)
        except:
            g = VKGroup()
        g.sid = group.get('id')
        g.title = group.get('name')
        g.user = user
        g.save()

    user.profile.last_vk_refresh = timezone.now()
    user_data = api.users.get(fields='photo_100')[0]
    user.profile.vk_name = user_data.get('first_name') + " " + user_data.get('last_name')
    user.profile.vk_avatar = user_data.get('photo_100')
    user.profile.vk_id = user_data.get('id')
    user.profile.vk_is_connected = True
    user.profile.save()

@receiver(AUTHORIZE_GROUP)
def authorize_group(access_token, group_id, user, **kwargs):
    group = VKGroup.objects.get(sid=group_id, user=user)
    group.access_token = access_token
    group.save()
    session = vk_api.VkApi(token=access_token,
                           app_id=settings.VK_CONF['APP_ID'],
                           scope='messages',
                           captcha_handler=captcha_handler)
    session.auth()
    api = session.get_api()
    
    t = Thread(target=load_subscribers,
               kwargs={'api': api, 'group': group, 'user': user,
                       'group_id': group_id})
    t.start()

def load_subscribers(api=None, subscribers=None, dialogs=None, group=None,
                     user=None, group_id=None):    
    dialogs = api.messages.getDialogs().get('items')
    subscribers = []
    offset = 0
    while True:
        result = api.groups.getMembers(group_id=group_id, offset=offset,
                                       fields='photo_50').get('items')
        if not result:
            break
        subscribers.extend(result)
        offset += 1000
        time.sleep(1/3)
    subscribers_ids = [s.get('id') for s in subscribers]
    for d in dialogs:
        if d.get('message').get('user_id') not in subscribers_ids:
            continue
        try:
            vkuser = VKUser.objects.get(sid=d.get('message').get('user_id'),
                                        group=group, user=user)
        except:
            vkuser = VKUser()
        vkuser.sid = d.get('message').get('user_id')
        user_info = api.users.get(user_id=vkuser.sid)[0]
        vkuser.first_name = user_info.get('first_name')
        vkuser.last_name = user_info.get('last_name')
        vkuser.isAllowedMessages = True
        vkuser.status = VKUser.ACTIVE
        vkuser.group = group
        vkuser.user = user
        vkuser.save()

    for s in subscribers:
        try:
            vkuser = VKUser.objects.get(sid=s.get('id'), group=group, user=user)
        except:
            vkuser = VKUser()
            vkuser.sid = s.get('id')
            vkuser.group = group
            vkuser.user = user
        vkuser.first_name = s.get('first_name')
        vkuser.last_name = s.get('last_name')
        
        is_allowed = get_msg_access(api, group_id=group_id, user_id=s.get('id'))
        vkuser.isAllowedMessages = is_allowed
        if is_allowed:
            vkuser.status = VKUser.ACTIVE
        else:
            vkuser.status = VKUser.INACTIVE
        vkuser.save()
    group.last_import = timezone.now()
    active_users = VKUser.objects.filter(group=group, user=user,
                                         status=VKUser.ACTIVE)
    if active_users.count() > 0:
        group.error_msg = None
    else:
        group.error_msg = "В группе нет пользователей, разрешивших писать им"
    group.save()

def get_msg_access(api, group_id=None, user_id=None):
    if not user_id or not group_id:
        raise Exception("Provide user_id and group_id")
    is_allowed = api.messages.isMessagesFromGroupAllowed(group_id=group_id,
                                                         user_id=user_id)
    if is_allowed.get('is_allowed') == 1:
        return True
    return False

def vk_send_message(msg_text, user_id=None, group_id=None):
    if not user_id:
        raise Exception("Provide user_id")
    user = VKUser.objects.get(id=user_id)
    if not group_id:
        group = user.group
    else:
        group = VKGroup.objects.get(id=group_id)
    if not group.access_token:
        raise Exception("Group is not aithorized")
    session = vk_api.VkApi(token=group.access_token,
                           app_id=settings.VK_CONF['APP_ID'],
                           scope='messages',
                           captcha_handler=captcha_handler)
    session.auth()
    api = session.get_api()
    sid = api.messages.send(user_id=user.sid, message=msg_text)
    msg = VKMessage()
    msg.sid = sid
    msg.user = group.user
    msg.recipient = user
    msg.sent = timezone.now()
    msg.save()
    return True

@receiver(SEND_MAILING_VK)
def vk_send_mailing_wrapper(msg_text=None, group_id=None, umailing=None, **kwargs):
    t = Thread(target=vk_send_mailing,
               kwargs={"msg_text": msg_text, "group_id": group_id,
                       'umailing': umailing})
    t.start()

def vk_send_mailing(msg_text=None, group_id=None, umailing=None, **kwargs):
    group = VKGroup.objects.get(id=group_id)
    if not group.access_token:
        raise Exception("Group is not authorized")
    users = VKUser.objects.filter(group=group, status=VKUser.ACTIVE)
    if not users:
        return False
    segment = VKSegment.objects.create(user=group.user)
    segment.add_users(users)
    mailing = VKMailing.objects.create(user=group.user, sent=timezone.now(),
                                       content=msg_text, group=group, segment=segment)
    umailing.vk_mailing = mailing
    umailing.save()

    mailing.send()
    return True

def save_as_draft_vk(msg_text=None, group_id=None, umailing=None, **kwargs):
    t = Thread(target=save_as_draft_vk_async,
               kwargs={"msg_text": msg_text, "group_id": group_id,
                       'umailing': umailing})
    t.start()

def save_as_draft_vk_async(msg_text=None, group_id=None, umailing=None, **kwargs):
    group = VKGroup.objects.get(id=group_id)
    if not group.access_token:
        raise Exception("Group is not authorized")
    users = VKUser.objects.filter(group=group, status=VKUser.ACTIVE)
    if not users:
        return False
    mailing = VKMailing.objects.create(user=group.user, sent=timezone.now(),
                                       content=msg_text, group=group)
    umailing.vk_mailing = mailing
    umailing.save()
    segment = VKSegment.objects.create(mailing=mailing, user=group.user)
    segment.add_users(users)
    return True

@receiver(START_MAILING_SEND)
def vk_send_mailing_start(group=None, content=None, mailing=None, **kwargs):
    """
    Using api.messages.send
    """
    session = vk_api.VkApi(token=group.access_token,
                           app_id=settings.VK_CONF['APP_ID'],
                           scope='messages', captcha_handler=captcha_handler)
    session.auth()
    api = session.get_api()
    sent, failed = 0, 0
    segment = mailing.get_segment()
    for user in segment.users.all():
        msg = VKMessage.objects.create(user=group.user, recipient=user,
                                       mailing=mailing,
                                       sent=timezone.now())
        try:
            sid = api.messages.send(user_id=user.sid, message=content)
            msg.status = VKMessage.SENT
            msg.sid = sid
            sent += 1
        except:
            msg.status = VKMessage.FAILED
            failed += 1
        finally:
            msg.save()
            time.sleep(1/3)
    if sent > 0 and failed == 0:
        mailing.status = mailing.COMPLETED
    elif sent == 0 and failed > 0:
        mailing.status = mailing.FAILED
    elif sent > 0 and failed > 0:
        mailing.status = mailing.PARTIALLY_COMPLETED
    mailing.save()

def check_read(group, msgs):
    """
    Using api.message.getById

    Bulk message retrieving by Ids and uppdating read state
    """
    api = api_init(group)
    start, end, total = 0, 99, msgs.count()
    while True:
        arr = [str(msg.sid) for msg in msgs[start:end]]
        if not arr:
            break
        try:
            msgs_dict = api.messages.getById(message_ids=",".join(arr)).get('items')
        except ApiError:
            api = api_init(group)
            msgs_dict = api.messages.getById(message_ids=",".join(arr)).get('items')
        for msg_dict in msgs_dict:
            if msg_dict.get('read_state') == 1:
                read = True
            else:
                read = False
            yield msgs.get(sid=msg_dict.get('id')), read
        if end >= total:
            break
        start += 100; end+= 100

# @receiver(UPDATE_READ_STATE)
# def update_read_state(mailing, **kwargs):
#     t = Thread(target=update_read_state_async, args=(mailing,))
#     t.start()

def update_read_state(mailing):
    msgs = VKMessage.objects.filter(mailing=mailing, status__lt=VKMessage.READ,
                                    sid__isnull=False)
    for msg, read_state in check_read(mailing.group, msgs):
        if read_state and msg.status != VKMessage.READ:
            msg.status = VKMessage.READ
            msg.save()
    if VKMessage.objects.filter(mailing=mailing, status__lt=VKMessage.READ,
                                sid__isnull=False)\
                        .exclude(status__lte=VKMessage.DRAFT).count() == 0:
        mailing.read_state_update = VKMailing.UPDATE_COMPLETED
        mailing.save()
    return
