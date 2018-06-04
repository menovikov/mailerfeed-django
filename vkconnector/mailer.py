import time
from threading import Thread

from django.dispatch import Signal, receiver
from django.conf import settings
from django.utils import timezone
import vk_api
from vk_api.exceptions import ApiError

from .models import VKGroup, VKUser, VKMessage, VKMailing, VKSegment


class VKMailer:
    """

    class for handling vk.com related actions

    """
    user = None

    # vk_user = None
    # vk_group = None
    
    access_token = ""

    def __init__(self, access_token=None, *args, **kwargs):
        if not access_token:
            raise Exception("Provide access_token")
        self.session = vk_api.VkApi(
            token=access_token,
            app_id=settings.VK_CONF['APP_ID'],
            scope='offline', captcha_handler=self._captcha_handler)
        self.session.auth()
        self.api = self.session.get_api()

    def _captcha_handler(self, captcha):
        key = None
        return captcha.try_again(key)

    def refresh_user(self, vk_user):
        user_info = self.api.users.get(user_id=vk_user.sid)[0]
        vk_user.first_name = user_info.get('first_name')
        vk_user.last_name = user_info.get('last_name')

    def get_groups(self, user):
        groups = self.api.groups.get(extended=True, filter='admin')['items']
        for group in groups:
            try:
                g = VKGroup.objects.get(sid=group.get('id'), user=user)
            except:
                g = VKGroup()
            g.sid = group.get('id')
            g.title = group.get('name')
            g.user = user
            g.save()

        user_data = self.api.users.get(fields='photo_100')[0]

        profile = user.profile
        profile.vk_name = user_data.get('first_name') + " " + user_data.get('last_name')
        profile.vk_avatar = user_data.get('photo_100')
        profile.vk_id = user_data.get('id')
        profile.vk_is_connected = True
        profile.last_vk_refresh = timezone.now()
        profile.save()

    def authorize_group(self, group_id, user, **kwargs):
        group = VKGroup.objects.get(sid=group_id, user=user)
        group.access_token = self.access_token
        group.save()        
        t = Thread(target=self.load_subscribers,
                   kwargs={'group': group, 'user': user, 'group_id': group_id})
        t.start()

    def load_subscribers(self, subscribers=None, dialogs=None, group=None,
                         user=None, group_id=None):    
        dialogs = self.api.messages.getDialogs().get('items')
        subscribers = []
        offset = 0

        while True:
            result = self.api.groups.getMembers(
                group_id=group_id,
                offset=offset,
                fields='photo_50').get('items')
            if not result:
                break
            subscribers.extend(result)
            offset += 1000
            time.sleep(1/3)

        subscribers_ids = [s.get('id') for s in subscribers]

        for s in subscribers:
            try:
                vkuser = VKUser.objects.get(
                    sid=s.get('id'),
                    group=group,
                    user=user)
            except:
                vkuser = VKUser()
                vkuser.sid = s.get('id')
                vkuser.group = group
                vkuser.user = user
            vkuser.first_name = s.get('first_name')
            vkuser.last_name = s.get('last_name')
            
            is_allowed = self.get_msg_access(
                group_id=group_id,
                user_id=s.get('id'))

            vkuser.isAllowedMessages = is_allowed
            if is_allowed:
                vkuser.status = VKUser.ACTIVE
            else:
                vkuser.status = VKUser.INACTIVE
            vkuser.save()
        group.last_import = timezone.now()
        active_users = VKUser.objects.filter(
            group=group,
            user=user,
            status=VKUser.ACTIVE)
        if active_users.count() > 0:
            group.error_msg = None
        else:
            group.error_msg = "В группе нет пользователей, разрешивших писать им"
        group.save()

    def create_segment(self, title=None, user_ids=[], group=None, user=None):
        if not title or not user_ids or not group:
            raise Exception("Invalid parameters")
        segment = VKSegment()
        segment.title = title
        segment.group = group
        segment.user = user
        segment.save()
        users = []
        for id in user_ids:
            try:
                users.append(VKUser.objects.get(id=int(i)))
            except:
                pass
        if not users:
            raise Exception("Users list is empty")
        segment.add_users(users)
        print(segment.id)
        return
