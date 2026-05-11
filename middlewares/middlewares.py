import threading

try:
    from opencensus.ext.django.middleware import OpencensusMiddleware
except Exception:  # pragma: no cover - optional dependency for local/dev
    OpencensusMiddleware = None

from django.http import HttpResponse

# from reversion.middleware import RevisionMiddleware


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

        # workaround for safelink check:
        if request.method == "HEAD":
            return HttpResponse(status=200)

        setattr(_threadlocal, "request", request)
        return self.get_response(request)


class OpencensusMiddlewareCompat(OpencensusMiddleware):
    """Compatibility wrapper for Django 5.2 middleware interface."""

    async_capable = False
    sync_capable = True

    def __init__(self, get_response=None):
        super().__init__(get_response)
        # Django 5.2 expects this attribute on middleware instances.
        self.async_mode = False


# Without this class the 'request revision' still works fine.
# TODO: how to make it effective?
# class BypassRevisionMiddleware(RevisionMiddleware):
#
#     def request_creates_revision(self, request):
#         # Bypass the revision according to ...
#         silent = request.META.get("HTTP_X_NOREVISION", "false")
#         return super().request_creates_revision(request) and \
#             silent != "true"
