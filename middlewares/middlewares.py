import threading

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
        if request.method == 'HEAD':
            return
        # return response
        setattr(_threadlocal, "request", request)
        return self.get_response(request)


# Without this class the 'request revision' still works fine.
# TODO: how to make it effective?
# class BypassRevisionMiddleware(RevisionMiddleware):
#
#     def request_creates_revision(self, request):
#         # Bypass the revision according to ...
#         silent = request.META.get("HTTP_X_NOREVISION", "false")
#         return super().request_creates_revision(request) and \
#             silent != "true"
