from re import sub
from django.conf import settings
from django.middleware.cache import FetchFromCacheMiddleware, UpdateCacheMiddleware
from django.utils.cache import get_cache_key
from rest_framework.views import APIView


def get_cache_key_prefix(request):
    cache_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
    drf_request = APIView().initialize_request(request)

    if drf_request.user.is_anonymous:
        user_id = 'anonymous'
    else:
        user_id = drf_request.user.id
    if not cache_prefix:
        return f'user_{user_id}'
    
    return f'{cache_prefix}_user_{user_id}'

class UpdateCacheForUserMiddleware(UpdateCacheMiddleware):
    def process_response(self, request, response):
        self.key_prefix = get_cache_key_prefix(request)
        return super().process_response(request, response)

class FetchFromCacheForUserMiddleware(FetchFromCacheMiddleware):
    def process_request(self, request):
        self.key_prefix = get_cache_key_prefix(request)
        return super().process_request(request)
