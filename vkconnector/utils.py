from django.core.urlresolvers import reverse
from django.conf import settings

VK_LINKS = {
	'user_auth' : 'https://oauth.vk.com/authorize?client_id={app_id}&display=popup&redirect_uri={redirect_uri}&scope=groups,offline&response_type=token&v=5.63',
	'group_auth': 'https://oauth.vk.com/authorize?client_id={app_id}&display=popup&redirect_uri={redirect_uri}&scope=messages&group_ids={group_id}&response_type=code&v=5.63',
	'group_code': 'https://oauth.vk.com/access_token?client_id={app_id}&client_secret={secret}&redirect_uri={redirect_uri}&code={code}',
}


class LinkManager:

	@staticmethod
	def get_link(social_network=None, case=None, *args, **kwargs):
		if not case or not social_network:
			raise Exception("Provide social network and case")

		if social_network == 1:
			return LinkManager._get_vk_link(case, *args, **kwargs)
		else:
			raise NotImplementedError("Func is not inplemented yet")

	@staticmethod
	def _get_vk_link(case, *args, **kwargs):
		if case == "redirect":
			request = kwargs.pop('request')
			# return request.scheme + '://' + request.get_host() + reverse('vk_auth_redirect')
			return settings.DOMAIN + reverse('vk_auth_redirect')
		return VK_LINKS.get(case)
		