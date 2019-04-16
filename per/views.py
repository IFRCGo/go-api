import json, datetime, pytz
from django.http import JsonResponse, HttpResponse
from api.views import (
    bad_request,
    bad_http_request,
    PublicJsonPostView,
    PublicJsonRequestView,
)
from .models import Form, FormData

def create_form(raw):

    form = Form.objects.create(code         = raw['code'],
                               name         = raw['name'],
                               language     = raw['language'],
                               ip_address   = raw['ip_address'],
                               unique_id    = raw['unique_id'],
                               started_at   = raw['started_at'],
                               ended_at     = raw['ended_at'],
                               submitted_at = raw['submitted_at'],
                               comment      = raw['comment'],
                               validated    = raw['validated'],
                               finalized    = raw['finalized'],
                               )
    form.save()
    return form

def create_form_data(raw, form):

    form_data = FormData.objects.create(form= form,
                            question_id     = raw['id'],
                            selected_option = raw['op'],
                            notes           = raw['nt'],
                            )
    form_data.save()
    return form_data

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

        currentDT = datetime.datetime.now(pytz.timezone('UTC'))
        if 'started_at' not in body:
            body['started_at']   = str(currentDT)
        if 'ended_at' not in body:
            body['ended_at']     = str(currentDT)
        if 'submitted_at' not in body:
            body['submitted_at'] = str(currentDT)
        if 'comment' not in body:
            body['comment'] = None
        if 'validated' not in body:
            body['validated'] = False
        if 'finalized' not in body:
            body['finalized'] = False


        missing_fields = [field for field in required_fields if field not in body]
        if len(missing_fields):
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        if ' ' in body['code']:
            return bad_request('Code can not contain spaces, please choose a different one.')

        try:
            form = create_form(body)
        except:
            return bad_request('Could not insert PER form record.')

        if 'data' in body:
            for rubr in body['data']:
                try:
                    create_form_data(rubr, form)
                except:
                    return bad_request('Could not insert PER formdata record.')

        return JsonResponse({'status': 'ok'})

# *** Test script from bash (similar to test_views.py, but remains in db):
# curl --header "Content-Type: application/json" \
#  --request POST \
#  --data '{
#            "code": "A1",
#            "name": "Nemo",
#            "language": 1,
#            "unique_id": "1aad9295-ceb9-4ad5-9b10-84cc423e93f4",
#            "started_at": "2019-04-11 11:42:22.278796+00",
#            "submitted_at": "2019-04-11 09:42:52.278796+00",
#            "data": [{"id": "1.1", "op": 3, "nt": "notes here"}, {"id": "1.2", "op": 0, "nt": "notes here also"}]
#             }' \
#  http://localhost:8000/sendperform
#  *** Afterpurger:
#  delete from per_formdata where notes like 'notes here%'; delete from per_form where name='Nemo';
