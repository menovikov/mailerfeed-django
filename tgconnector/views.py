from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required

from common.utils import validate_phone

from .models import TGUser
from .tgmailer import send_code, authorize, refresh

@login_required
def tg_user_auth(request):
	if request.POST:
		phone = request.POST.get('phone')
		sent, error = send_code(request.user, phone)
		if sent:
			data = {'status': 'ok'}
		else:
			data = {'status': 'failed', 'msg': error}
		return JsonResponse(data, safe=False)
	return HttpResponse(status=405)

@login_required
def tg_check_code(request):
	if request.POST:
		code = request.POST.get('code')
		authorized, error = authorize(request.user, code)
		if authorized:
			data = {'status': 'ok'}
		else:
			data = {'status': 'failed', 'msg': error}
		return JsonResponse(data, safe=False)
	return HttpResponse(status=405)

@login_required
def tg_refresh(request):
	if request.POST:
		refreshed, error = refresh(request.user)
		if refreshed:
			data = {'status': 'ok'}
		else:
			data = {'status': 'failed', 'msg': error}
		return JsonResponse(data, safe=False)
	return HttpResponse(status=405)

@login_required
def get_tg_subs(request):
	if request.POST:
		subs = TGUser.objects.filter(user=request.user)
		arr = []
		for sub in subs:
			arr.append({
					'id': sub.id,
					'name': sub.get_full_name(),
				})
		return JsonResponse({'items': arr, 'count': len(arr)}, safe=False)
	return HttpResponse(status=405)

@login_required
def tg_logout(request):
	request.user.profile.tg_is_connected = False
	request.user.profile.save()
	return redirect("networks")
