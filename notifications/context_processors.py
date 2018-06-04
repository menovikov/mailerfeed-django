from datetime import timedelta

from django.utils import timezone
from django.conf import settings

from .models import WebNotification

def web_notifications(request):
	if request.user.is_authenticated():
		return {
			'notifications': WebNotification.objects.filter(
				user=request.user,
				level=request.user.profile.notification_level,
				created__gte=timezone.now() - timedelta(**settings.NOTIFICATIONS_DURING))
		}
	else:
		return {}
