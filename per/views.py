import json
from django.http import JsonResponse, HttpResponse
from api.views import (
    bad_request,
    bad_http_request,
    PublicJsonPostView,
    PublicJsonRequestView,
)
from .models import Form

def create_form(raw):

    form = Form.objects.create(code=raw['code'],
                               name=raw['name'],
                               language=raw['language'],
                               ip_address=raw['ip_address'],
                               finalized=False,
                               )
    return form

class FormSent(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        body = json.loads(request.body.decode('utf-8'))

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            body['ip_address'] = x_forwarded_for.split(',')[-1].strip()
        else:
            body['ip_address'] = request.META.get('REMOTE_ADDR')

        required_fields = [
            'code',
            'name',
            'language',
        ]

        missing_fields = [field for field in required_fields if field not in body]
        if len(missing_fields):
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        if ' ' in body['code']:
            return bad_request('Code can not contain spaces, please choose a different one.')

        try:
            form = create_form(body)
        except:
            return bad_request('Could not insert PER form record.')

        form.save()

        return JsonResponse({'status': 'ok'})
