from django.conf import settings
from django.middleware.cache import FetchFromCacheMiddleware, UpdateCacheMiddleware

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView


def check_if_user_is_anonymous(request):
    try:
        return request.user.is_anonymous
        # NOTE: Add exception for each authenticator
    except AuthenticationFailed:
        return True


def get_cache_key_prefix(request):
    if settings.DISABLE_API_CACHE:
        return None

    cache_prefix = settings.CACHE_MIDDLEWARE_KEY_PREFIX
    drf_request = APIView().initialize_request(request)

    if check_if_user_is_anonymous(drf_request):
        return f'{cache_prefix}_anonymous'


class UpdateCacheForUserMiddleware(UpdateCacheMiddleware):
    def process_response(self, request, response):
        if key_prefix := get_cache_key_prefix(request):
            self.key_prefix = key_prefix
            return super().process_response(request, response)
        return response


class FetchFromCacheForUserMiddleware(FetchFromCacheMiddleware):
    def process_request(self, request):
        if key_prefix := get_cache_key_prefix(request):
            self.key_prefix = key_prefix
            return super().process_request(request)
