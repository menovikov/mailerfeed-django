from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static

urlpatterns = [
    url(r'^auth/', include('user_registration.backends.default.urls')),
    url(r'^vk/', include('vkconnector.urls')),
    url(r'tg/', include('tgconnector.urls')),
    url(r'click/', include('linker.urls')),
    url(r'triggers/', include('triggers.urls')),
    url(r'', include('common.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
