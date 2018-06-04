import json

from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse, Http404

from .models import Trigger, TriggerChainItem
from vkconnector.models import VKGroup
from common.models import SocialObject, UMailing


@login_required
def triggers(request):
	"""
	Triggers list
	"""
	triggers = request.user.profile.get_triggers()
	context = {
		'triggers': triggers,
	}
	return render(request, 'triggers/triggers.html', context)

@login_required
def triggers_detail(request, id=None):
	"""
	Trigger details displayed;
	Trigger editing done through async requests via ajax
	"""
	trigger = None
	if id:
		try:
			trigger = Trigger.objects.get(id=id)
			if not request.user.is_staff and request.user != trigger.user:
				return Http404
		except Trigger.DoesNotExist:
			return Http404
	if not request.POST and not request.is_ajax():
		context = {
			'trigger': trigger,
			'units': TriggerChainItem.UNITS,
			'mailings': request.user.profile.get_mailings(),
			'start_options': Trigger.START_CHOICES,
			'channels': SocialObject.SOCIAL_NETWORKS,
			'vk_groups': request.user.profile.get_admin_groups().filter(
				access_token__isnull=False),
		}
		return render(request, 'triggers/triggers_detail.html', context)
	if request.is_ajax():
		data = json.loads(request.body.decode('utf-8'))
		title, start, channel, start_type = None, None, None, None
	
		title = data.get('title')
		start = int(data.get('start'))
		try:
			channel = int(data.get('channel'))
		except:
			return JsonResponse(
				{'status': 'failed', 'msg_text': "Канал не выбран"},
				safe=False)
		
		if not trigger:
			trigger = Trigger(user=request.user)		
		if title and title != trigger.title:
			trigger.title = title
		if start and trigger.time_from != start:
			trigger.time_from = start
		if start == Trigger.MAILING:
			try:
				mailing_id = int(data.get('mailing_id'))
				mailing = UMailing.objects.get(id=mailing_id)
				trigger.mailing = mailing
			except Exception as e:
				return JsonResponse(
					{'status': 'failed', 'msg_text': "Рассылка не выбрана"},
					safe=False)
		if channel:
			if channel == SocialObject.VK:
				trigger.channel = SocialObject.VK
				try:
					vk_group = VKGroup.objects.get(id=int(int(data.get('vk_group'))))
					trigger.group = vk_group
				except VKGroup.DoesNotExist:
					return JsonResponse(
						{'status': 'failed', 'msg_text': "Группы не существует"},
						safe=False)
				except Exception as e:
					return JsonResponse(
						{'status': 'failed', 'msg_text': "Группа не выбрана"},
						safe=False)
			elif channel == SocialObject.TG:
				if trigger.time_from == Trigger.SUBSCRIPTION:
					return JsonResponse(
						{'status': 'failed', 'msg_text': "Цепочка по подписке не активна для telegram.org"},
						safe=False)
				trigger.channel = SocialObject.TG
		trigger.save()
		if int(data.get('count')) > 0:
			trigger.get_actions().delete()

		for i in range(int(data.get('count'))):
			action_data = data['items'][str(i)]
			a = TriggerChainItem.objects.create(
				trigger=trigger,
				title=action_data.get('msg_name'),
				text=action_data.get('msg_text'),
			)
			a.start_after = int(action_data.get('start'))
			a.save()

		validated, msg_text = trigger.validate()
		if validated:
			data = {'status': 'ok', 'msg_text': 'success'}
		else:
			data = {'status': 'failed', 'msg_text': msg_text}

		return JsonResponse(data, safe=False)
	return HttpResponse(status=405)

@login_required
def get_mailings(request):
	if not request.POST:
		return HttpResponse(status=405)
	data = request.POST
	try:
		channel = int(data.get('channel'))
		mailings = request.user.profile.get_mailings()
		try:
			trigger_id = int(data.get('trigger_id'))
			trigger = Trigger.objects.get(id=trigger_id)
			mailing_active = trigger.mailing
		except Exception as e:
			mailing_active = None
		if channel == SocialObject.VK:
			mailings = mailings.filter(vk_mailing__isnull=False)
			vk_group_id = int(data.get('vk_group_id'))
			try:
				vk_group = VKGroup.objects.filter(id=vk_group_id)
				mailings.filter(vk_mailing__group=vk_group)
			except VKGroup.DoesNotExist:
				return HttpResponse(status=404)
		elif channel == SocialObject.TG:
			mailings = mailings.filter(tg_mailing__isnull=False)
	except Exception as e:
		return HttpResponse(status=400)
	return JsonResponse(
		{'mailings': [
			{
			"id": m.id, 
			"title": m.title, 
			"isActive": True if m == mailing_active else False
			} for m in mailings]
		},
		safe=False)

@login_required
def triggers_setstatus(request, id=None, status=None):
	"""
	Changing status of a trigger
	"""
	try:
		trigger = Trigger.objects.get(id=id)
	except Trigger.DoesNotExist:
		return Http404
	if trigger.user != request.user and not request.user.is_staff:
		return Http404
	if not status:
		return HttpResponse(status=400)
	trigger.status = int(status)
	if trigger.status == Trigger.STARTED \
	and trigger.time_from == Trigger.MAILING:
		trigger.save()
		trigger.schedule()
	else:
		trigger.save()
	return redirect(triggers)

@login_required
def triggers_delete(request, id=None):
	"""
	Synchronous deletion of a trigger 
	"""
	try:
		trigger = Trigger.objects.get(id=id)
	except Trigger.DoesNotExist:
		return Http404
	if trigger.user != request.user and not request.user.is_staff:
		return Http404
	trigger.delete()
	return redirect(triggers)
