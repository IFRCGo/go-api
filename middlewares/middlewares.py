import threading

from rest_framework import permissions
from django.conf import settings
from django.http import JsonResponse
from django.utils.translation import ugettext, get_language


_threadlocal = threading.local()


def get_signal_request():
    """
    !!! Do not use if your operation is asynchronus !!!
    Allow to access current request in signals
    This is a hack that looks into the thread
    Mainly used for log purpose
    """

    return getattr(_threadlocal, "request", None)


def get_username():
    req = get_signal_request()
    if req and req.user:
        return req.user.username
    else:
        return None


class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # # Code to be executed for each request before
        # # the view (and later middleware) are called.
        # self.thread_local.current_request = request

        # response = self.get_response(request)

        # # Code to be executed for each request/response after
        # # the view is called.

        # return response
        setattr(_threadlocal, "request", request)
        return self.get_response(request)

    def process_view(self, request, view_function, *args, **kwargs):
        # NOTE: For POST raise error on non default language
        request_match = request.resolver_match
        reject_the_request = (
            # is Non-safe methods
            (request and request.method not in permissions.SAFE_METHODS) and
            # is API Request
            request_match and request_match.route.startswith('^api/') and
            # is Non-english language
            get_language() != settings.LANGUAGE_CODE
        )
        if reject_the_request:
            return JsonResponse({
                'error': ugettext('Currently %(method)s method is only allowed for non-English language.') % {
                    'method': request.method
                },
            }, status=405)
