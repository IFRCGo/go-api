import json
from api.views import PublicJsonPostView, PublicJsonRequestView
from api.utils import pretty_request

class NewRegistration(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        print(pretty_request(request))
        body = json.loads(request.body.decode('utf-8'))
        print(body)
