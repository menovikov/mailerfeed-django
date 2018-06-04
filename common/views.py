import logging

from django.shortcuts import render, redirect
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import FileSystemStorage

from validate_email import validate_email

from .forms import UploadFileForm
from .models import SocialObject, UMailing
from .utils import validate_pass, validate_phone, validate_int, paginator
from vkconnector.models import VKGroup, VKUser, VKMessage, VKMailing, VKSegment
from vkconnector.mailer import VKMailer
from tgconnector.models import TGUser


logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
	profile = request.user.profile
	context = {
		'subscribers_count': profile.get_subscribers(count=True),
		'mailings_count': profile.get_mailings().count(),
		'messages_count': profile.get_messages(count=True),
	}
	return render(request, 'dashboard/dashboard.html', context)

@login_required
def social_networks(request):
	return render(request, 'channels/social_networks.html', {})

def redirect_url(request):
	if request.user.is_authenticated:
		return redirect('dashboard')
	else:
		return redirect('auth_login')

@login_required
def mailings(request):
	profile = request.user.profile
	mailings = profile.get_mailings()
	context = {
		'subs_total_count': profile.get_subscribers(count=True),
		'subs_active_count': profile.get_subscribers(active=True, count=True),
		'mailings': mailings,
		'mailings_count': mailings.count(),
		'messages_count': profile.get_messages(count=True),
		'vk_groups': profile.get_admin_groups(),
	}
	return render(request, 'mailings/mailings.html', context)

@login_required
def mailings_detail(request, id=None):
	mailing = UMailing.objects.get(id=id)
	if not request.user.is_superuser and mailing.user != request.user:
		return HttpResponse(status=403)
	total = mailing.get_msgs_count(total=True)
	sent = mailing.get_msgs_count(sent=True)
	sent_p = int(sent / total * 100) if total > 0 else 0
	context = {
		'mailing': mailing,
		'total_msgs_count': total,
		'sent_msgs_p': sent_p,
	}
	return render(request, 'mailings/mailings_detail.html', context)

@login_required
def mailings_detail_stat(request):
	if not request.POST:
		return HttpResponse(status=405)
	id_ = request.POST.get('mailing_id')
	if not id_:
		return HttpResponse(status=400)
	try:
		mailing = UMailing.objects.get(id=id_)
	except UMailing.DoesNotExist:
		return HttpResponse(status=404)
	if not request.user.is_superuser and mailing.user != request.user:
		return HttpResponse(status=403)
	mailing.update_read_state()
	total = mailing.get_msgs_count(total=True)
	opened = mailing.get_msgs_count(opened=True)
	opened_p = int(opened / total * 100) if total > 0 else 0
	stat_box_openings = render_to_string('inc/mailings_detail/stat_box.openings.html',
							   		{'opened': opened, 'opened_p': opened_p, 'total': total})
	msgs_items = render_to_string('inc/mailings_detail/messages.html',
								 {'msgs': mailing.get_messages()})
	return JsonResponse({'msgs_items': msgs_items, 
						 'stat_box_openings': stat_box_openings},
						safe=False)

@login_required
def mailings_detail_clicks_stat(request):
	if not request.POST:
		return HttpResponse(status=405)
	id_ = request.POST.get('mailing_id')
	if not id_:
		return HttpResponse(status=400)
	try:
		mailing = UMailing.objects.get(id=id_)
	except UMailing.DoesNotExist:
		return HttpResponse(status=404)
	if not request.user.is_superuser and mailing.user != request.user:
		return HttpResponse(status=403)
	clicked, clicked_unique = 0, 0
	locations = []
	links = mailing.get_links()
	if links:
		for link in links:
			clicked += link.get_clicks().count()
			clicks_unique = link.get_clicks(unique=True)
			if clicks_unique.count() > 0:
				for agent, addr, lat, lon in clicks_unique:
					if addr and lat and lon:
						locations.append([addr, lat, lon, 1])
			clicked_unique += clicks_unique.count()
	
	stat_box_clicks = render_to_string('inc/mailings_detail/stat_box.clicks.html',
							   		  {'clicked': clicked, 'clicked_unique': clicked_unique})
	# msgs_items = render_to_string('inc/mailings_detail/messages.html',
	# 							 {'msgs': mailing.get_messages()})
	return JsonResponse({'stat_box_clicks': stat_box_clicks, 'markers': locations},
						safe=False)

@login_required
def segments(request):
	profile = request.user.profile
	context = {
		'segments': profile.get_segments().filter(title__isnull=False),
	}
	return render(request, 'segments/segments.html', context)

@login_required
def segments_detail(request, id=None):
	context = {
		'channels': SocialObject.SOCIAL_NETWORKS, 
		'vk_groups': request.user.profile.get_admin_groups(),
	}
	if id:
		try:
			segment = VKSegment.objects.get(id=id)
		except VKSegment.DoesNotExist:
			return HttpResponse(status=404)
		if segment.user != request.user and not request.user.is_superuser:
			return HttpResponse(status=403)
		context = {
			'segment': segment,
		}
	else:
		if request.method == 'POST' and request.FILES:
			print(request.POST)
			ids = []
			title = request.POST.get('title')
			channel = request.POST.get('channel')
			vk_group_id = request.POST.get('vk_group_id')
			if not title:
				return JsonResponse({
					'status': 'failed', 'msg_text': "No title provided"},
					safe=False)
			try:
				channel = int(channel)
				file = request.FILES['file']
				for chunk in file.chunks():
					ids.extend(chunk.decode('utf-8').split('\r\n'))

				if channel == SocialObject.VK:
					print()
					vk_group_id = int(vk_group_id)
					group = VKGroup.objects.get(id=vk_group_id)
					print("Found group")
					mailer = VKMailer(group.access_token)
					mailer.create_segment(
						user_ids=ids,
						group=group,
						title=title,
						user=request.user)
					return JsonResponse({"status": "ok"}, safe=False)
			except Exception as e:
				print(e)
				return JsonResponse({
					'status': 'failed', 'msg_text': str(e)},
					safe=False)
			
	return render(request, 'segments/segments_detail.html', context)

@login_required
def subscribers(request):
	if not request.POST:
		context = {
			'vk_groups': request.user.profile.get_admin_groups(),
		}
		return render(request, 'subscribers/subscribers.html', context)
	start, end, page, step = 0, 100, 1, 100
	include_vk = include_tg = include_active = include_inactive = False

	if request.POST.get('include_vk') == 'true':
		include_vk = True
	if request.POST.get('include_tg') == 'true':
		include_tg = True
	if request.POST.get('include_active') == 'true':
		include_active = True
	if request.POST.get('include_inactive') == 'true':
		include_inactive = True
	if not include_active and not include_inactive:
		include_vk = include_tg = False
	if validate_int(request.POST.get('page')):
		page = int(request.POST.get('page'))

	subscribers = request.user.profile.get_subscribers(
		vk=include_vk, tg=include_tg, active=include_active,
	   	inactive=include_inactive)
	subscribers_count = request.user.profile.get_subscribers(
		vk=include_vk, tg=include_tg, active=include_active,
	   	inactive=include_inactive, count=True)

	start, end, pagination_box = paginator(page, start, end, step, subscribers_count)
	subs = render_to_string(
		'inc/subscribers/subscribers_table.html',
		{'subs': subscribers[start:end]})
	pagination = render_to_string(
		'inc/subscribers/pagination.html', pagination_box)

	return JsonResponse({'subs_table': subs, 'pagination': pagination},
						safe=False)	

@login_required
def subscribers_growth(request):
	context = {
		'vk_groups': request.user.profile.get_admin_groups(),
	}
	return render(request, 'subscribers/subscribers_growth.html', context)

@login_required
def profile(request):
	if request.POST:
		errors = []
		profile = request.user.profile
		if request.POST.get('first_name'):
			profile.first_name = request.POST.get('first_name')
		if request.POST.get('last_name'):
			profile.last_name = request.POST.get('last_name')
		if request.POST.get('email'):
			if not validate_email(request.POST.get('email')):
				errors.append("Указан неправильный емейл")
			profile.email = request.POST.get('email')
		if request.POST.get('phone'):
			if not validate_phone(request.POST.get('phone')):
				errors.append("Указан неправильный номер телефона")
			profile.phone = request.POST.get('phone')
		if request.POST.get('pass') and request.POST.get('pass2'):
			errors.extend(validate_pass(request.POST.get('pass'), request.POST.get('pass2')))
		if errors:
			resp = {"status": "failed", "msg": errors}
		else:
			profile.save()
			resp = {"status": "ok", "msg": ["Изменения сохранены"]}
		return JsonResponse(resp, safe=False)
	return render(request, 'profile/profile.html', {})

@login_required
def send_mailing(request):
	if not request.POST:
		return HttpResponse(status=405)
	if request.POST:
		result = {'status': 'failed', 'msg': 'Validation error'}
		vk_group_id = request.POST.get('vk_group_id')
		tg_ids = request.POST.getlist('tg_subs[]')
		msg_title = request.POST.get('msg_title')
		msg_text = request.POST.get('msg_text')

		if tg_ids or vk_group_id:
			m = UMailing.objects.create(
				title=msg_title,
				content=msg_text,
				user=request.user)
			validated = m.validate()
			if not validated:
				result = {'status': 'failed', 'msg': 'Validation error'}
			else:
				m.send(vk_group_id=vk_group_id, tg_ids=tg_ids)
				result = {'status': 'ok', 'msg': 'Success'}
		return JsonResponse({'data': result}, safe=False)

@login_required
def save_draft_mailing(request):
	if not request.POST:
		return HttpResponse(status=405)
	if request.POST:
		vk_group_id = request.POST.get('vk_group_id')
		tg_ids = request.POST.getlist('tg_subs[]')
		msg_text = request.POST.get('msg_text')
		# m = UMailing.objects.create(user=request.user, content=msg_text)
		# m.save_as_draft(vk_group_id=vk_group_id, tg_ids=tg_ids)
		return HttpResponse(status=200)
