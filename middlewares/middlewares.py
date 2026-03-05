import logging
import threading

from django.conf import settings
from django.http import HttpResponse

# from reversion.middleware import RevisionMiddleware


_threadlocal = threading.local()
logger = logging.getLogger("django")


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # X-Forwarded-For can be a list of IPs: client, proxy1, proxy2
        return x_forwarded_for.split(",")[0].strip()
    x_real_ip = request.META.get("HTTP_X_REAL_IP")
    if x_real_ip:
        return x_real_ip.strip()
    return request.META.get("REMOTE_ADDR")


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

        # workaround for safelink check:
        if request.method == "HEAD":
            if settings.LOG_REQUEST_IP:
                client_ip = get_client_ip(request)
                logger.info(
                    " %s %s %s | %s",
                    request.method,
                    request.path,
                    200,
                    client_ip,
                )
            return HttpResponse(status=200)

        setattr(_threadlocal, "request", request)
        request.client_ip = get_client_ip(request)
        response = self.get_response(request)
        if settings.LOG_REQUEST_IP:
            logger.info(
                " %s %s %s | %s",
                request.method,
                request.path,
                response.status_code,
                request.client_ip,
            )
        return response


# Without this class the 'request revision' still works fine.
# TODO: how to make it effective?
# class BypassRevisionMiddleware(RevisionMiddleware):
#
#     def request_creates_revision(self, request):
#         # Bypass the revision according to ...
#         silent = request.META.get("HTTP_X_NOREVISION", "false")
#         return super().request_creates_revision(request) and \
#             silent != "true"
