import logging
import requests
import json
from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404, JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from vk_api.exceptions import ApiError

from .models import VKGroup, VKMailing, VKUser, VKMessage
from .vkmailer import GET_GROUPS, AUTHORIZE_GROUP
from .vkmailer import vk_send_message, vk_send_mailing
from .utils import LinkManager

logger = logging.getLogger(__name__)


@login_required
def vk_user_auth(request):
	link = LinkManager.get_link(social_network=1, case='user_auth').format(
		app_id=settings.VK_CONF['APP_ID'],
		redirect_uri=LinkManager.get_link(request=request, social_network=1, case='redirect'))
	return redirect(link)

@login_required
def vk_auth_redirect(request):
	if request.GET:
		access_token, code, error = (
			request.GET.get('access_token'),
			request.GET.get('code'),
			request.GET.get('error'),
		)

		if access_token:
			user_id, expires_in = request.GET.get('user_id'), request.GET.get('expires_in')
			GET_GROUPS.send(access_token=access_token, user=request.user, sender=None)
		elif code:
			redirect_uri = LinkManager.get_link(
				request=request, social_network=1, case='redirect')
			link = LinkManager.get_link(
				social_network=1, case='group_code').format(
				app_id=settings.VK_CONF['APP_ID'], 
				secret=settings.VK_CONF['SECRET'],
				code=code, redirect_uri=redirect_uri)
			r = requests.get(link)
			data = json.loads(r._content.decode('utf-8'))
			access_token_list = [x for x in list(data.keys()) if 'access_token_' in x]
			if access_token_list:
				access_token_group = data.get(access_token_list[0])
				group_id = int(access_token_list[0].replace('access_token_', ''))
				try:
					AUTHORIZE_GROUP.send(
						access_token=access_token_group,
						group_id=group_id,
						user=request.user, sender=None)
				except ApiError as e:
					group = VKGroup.objects.get(sid=group_id, user=request.user)
					group.error_msg = e.error['error_msg']
					group.save()
			return redirect('mailings')
		elif error:
			error_reason = request.GET.get('error_reason')
			error_description = request.GET.get('error_description')
	if '?' in request.get_full_path():
		return redirect('dashboard')
	return render(request, 'vk/success.html', {})

@login_required
def vk_group_auth(request, group_id=None):
	vkid = VKGroup.objects.get(id=group_id).sid
	link = LinkManager.get_link(
		social_network=1, case='group_auth').format(
        app_id=settings.VK_CONF['APP_ID'], group_id=vkid,
        redirect_uri=LinkManager.get_link(request=request, social_network=1, case='redirect'))
	return redirect(link)

@login_required
def get_social_communities(request):
	if request.POST:
		social_network = request.POST.get('social_network')
		groups = VKGroup.objects.filter(user=request.user)
		result = []
		for group in groups:
			result.append({
					'value': group.id,
					'title': group.title,
					'sid': group.sid,
				})
		return JsonResponse({'data': result}, safe=False)
	return HttpResponse(status=400)

@login_required
def get_active_subscribers(request):
	if not request.user.is_authenticated:
		return HttpResponse(status=403)
	if request.POST:
		error_msg = ''
		social_network = request.POST.get('social_network')
		group_id = request.POST.get('group_id')
		subscribers = VKUser.objects.filter(user=request.user,
											status=VKUser.ACTIVE)
		if group_id:
			subscribers = subscribers.filter(group__id=group_id)
			group = VKGroup.objects.get(id=group_id)
			if group.error_msg:
				error_msg = group.error_msg
		count = subscribers.count()
		import_link = reverse(vk_group_auth, kwargs={'group_id': group_id})
		if count == 0 and not error_msg:
			error_msg = "Необходим импорт подписчиков" 
		return JsonResponse({'count': subscribers.count(), 'link': import_link,
							 'error_msg': error_msg}, safe=False)
	return HttpResponse(status=400)

def check_user_allowedMessages(request):
	if not request.user.is_authenticated:
		return HttpResponse(status=403)
	if request.POST:
		social_network = request.POST.get('social_network')
		group_id = request.POST.get('group_id')
		user_sid = request.user.profile.vk_id
		is_allowed = VKUser.check_user_allowedMessages(
			user_sid=user_sid, group_id=group_id)
		result = {'is_allowed': is_allowed}
		return JsonResponse({'data': result}, safe=False)
	return HttpResponse(status=400)

@login_required
def get_vk_widget(request):
	from triggers.models import Trigger

	if not request.POST:
		return HttpResponse(status=405)
	group_id = int(request.POST.get('group_id'))
	if not group_id:
		return HttpResponse(status=400)
	try:
		group = VKGroup.objects.get(id=group_id)
	except VKGroup.DoesNotExist:
		return HttpResponse(status=404)
	widget_code = render_to_string(
		'subscribers/widgets/subscribers_growth.vk-widget.txt', 
		{
			'user_id': request.user.id,
			'group_id': group.id,
			'group_sid': group.sid,
			'script_path': settings.DOMAIN \
				+ static('clientside/vk-widget%s.js' % ("-local" if settings.DEBUG else ""))

		})
	widget_code_safe = widget_code.replace('<', '&lt;').replace('>', '&gt;')
	return JsonResponse(
		{'widget_code_safe': widget_code_safe,
		'triggers_count': group.get_triggers().filter(status=Trigger.STARTED).count(),
		'widget_code': widget_code}, safe=False)

@csrf_exempt
def vk_subscriber_track(request):
	from triggers.models import Trigger

	if request.GET.get('user_id') and request.GET.get('allowed') \
	and request.GET.get('client'):
		data = request.GET
	elif request.POST.get('user_id') and request.POST.get('allowed') \
	and request.POST.get('client'):
		data = request.POST
		
		try:
			allowed = True if data.get('allowed') == 'true' else False
			user_sid = int(data.get('user_id'))
			user_id, group_id, _ = data.get('client').split('-')
			user = User.objects.get(id=int(user_id))
			vk_group = VKGroup.objects.get(id=int(group_id), user__id=user_id)
			try:
				vk_user = VKUser.objects.get(
					sid=user_sid, user=user, group=vk_group)
			except VKUser.DoesNotExist:
				vk_user = VKUser(
					sid=user_sid, user=user, group=vk_group,
					status=VKUser.ACTIVE)
				vk_user.save(refresh=True)

		except VKGroup.DoesNotExist:
			return HttpResponse(status=404)
		except Exception as e:
			return HttpResponse(status=400)
		if not allowed:
			return HttpResponse(status=200)
		triggers = vk_group.get_triggers().filter(time_from=Trigger.SUBSCRIPTION)
		for t in triggers:
			if t.status != t.STARTED:
				continue
			offset = timedelta(seconds=0)
			for act in t.get_actions():
				offset += act.start_after
				act.schedule(countdown=offset.seconds, to=vk_user)
	else:
		return HttpResponse(status=400)
	return HttpResponse(status=200)

@login_required
def vk_logout(request):
	request.user.profile.vk_is_connected = False
	request.user.profile.save()
	return redirect("networks")
