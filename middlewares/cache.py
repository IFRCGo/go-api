from django.conf import settings
from django.middleware.cache import FetchFromCacheMiddleware, UpdateCacheMiddleware
from rest_framework.views import APIView


def get_cache_key_prefix(request):
    cache_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
    drf_request = APIView().initialize_request(request)

    if drf_request.user.is_anonymous:
        return f'{cache_prefix}_anonymous'


class UpdateCacheForUserMiddleware(UpdateCacheMiddleware):
    def process_response(self, request, response):
        if key_prefix := get_cache_key_prefix(request):
            self.key_prefix = key_prefix
            return super().process_response(request, response)
        return response


class FetchFromCacheForUserMiddleware(FetchFromCacheMiddleware):
    def process_request(self, request):
        # FIXME: TinyMCE Image Upload CSRF check skip:
        if request.method == 'POST' \
        and request.path == '/upload_image' \
        and request._cors_enabled == True \
        and hasattr(request, 'META') \
        and 'HTTP_HOST' in request.META \
        and request.META['HTTP_HOST'] in \
        ('localhost:8000', 'goadmin-stage.ifrc.org', 'goadmin.ifrc.org'):
            request._dont_enforce_csrf_checks = True
        if key_prefix := get_cache_key_prefix(request):
            self.key_prefix = key_prefix
            return super().process_request(request)
