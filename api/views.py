import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from tastypie.models import ApiKey
from .utils import pretty_request
from .authentication import token_duration

@csrf_exempt
def get_auth_token(request):
    print(pretty_request(request))
    if request.META.get('CONTENT_TYPE') != 'application/json':
        return HttpResponseBadRequest('Content-type must be `application/json`')
    elif request.method != 'POST':
        return HttpResponseBadRequest('HTTP method must be `POST`')
    else:
        body = json.loads(request.body.decode('utf-8'))
        username = body['username']
        password = body['password']
        if not username or not password:
            return HttpResponseBadRequest('Body must contain `username` and `password`')

        user = authenticate(username=username, password=password)
        if user is not None:
            api_key, created = ApiKey.objects.get_or_create(user=user)
            return JsonResponse({
                'token': api_key.key,
                'username': username,
                'expires': api_key.created + token_duration,
            })
        else:
            return HttpResponseBadRequest('Could not authenticate')
