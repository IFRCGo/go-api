from django.shortcuts import render
import json, datetime, pytz
from django.http import JsonResponse
from api.views import (
    bad_request,
    bad_http_request,
    PublicJsonPostView,
    PublicJsonRequestView,
)
from .models import (
    Project
)

# Create your views here.

class CreateProject(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):

        body = json.loads(request.body.decode('utf-8'))

        return JsonResponse({'status': 'ok'})
