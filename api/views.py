import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from tastypie.models import ApiKey
from .utils import pretty_request
from .authentication import token_duration

@csrf_exempt
def get_auth_token(request):
    print(pretty_request(request))
    if request.META.get('CONTENT_TYPE') != 'application/json':
        return JsonResponse({
            'statusCode': 400,
            'message': 'Content-type must be `application/json`'
        }, status=400)

    elif request.method != 'POST':
        return JsonResponse({
            'statusCode': 400,
            'message': 'HTTP method must be `POST`'
        }, status=400)

    else:
        body = json.loads(request.body.decode('utf-8'))
        username = body['username']
        password = body['password']
        if not username or not password:
            return JsonResponse({
                'statusCode': 400,
                'message': 'Body must contain `username` and `password`'
            }, status=400)

        user = authenticate(username=username, password=password)
        if user is not None:
            api_key, created = ApiKey.objects.get_or_create(user=user)
            return JsonResponse({
                'token': api_key.key,
                'username': username,
                'first': user.first_name,
                'last': user.last_name,
                'expires': api_key.created + token_duration,
            })
        else:
            return JsonResponse({
                'statusCode': 400,
                'message': 'Could not authenticate'
            }, status=400)
