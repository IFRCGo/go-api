import json, datetime, pytz
from django.http import JsonResponse, HttpResponse
from api.views import (
    bad_request,
    bad_http_request,
    PublicJsonPostView,
    PublicJsonRequestView,
)
from .models import (
    Draft, Form, FormData
)

def create_draft(raw):
    Draft.objects.filter(code=raw['code'], user_id=raw['user_id']).delete()  # If exists (a previous draft), delete it.
    draft = Draft.objects.create(code       = raw['code'],
                               user_id      = raw['user_id'],
                               data         = raw['data'],
                               )
    draft.save()
    return draft

def create_form(raw):

    form = Form.objects.create(code         = raw['code'],
                               name         = raw['name'],
                               language     = raw['language'],
                               user_id      = raw['user_id'],
                               country_id   = raw['country_id'],
                               ns           = raw['ns'],
                               ip_address   = raw['ip_address'],
                               started_at   = raw['started_at'],
                               ended_at     = raw['ended_at'],
                               submitted_at = raw['submitted_at'],
                               comment      = raw['comment'],
                               validated    = raw['validated'],
                               finalized    = raw['finalized'],
                               # unique_id  = raw['unique_id'], # only KoBo form provided
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

        #if not request.user.is_authenticated:
        #    return bad_request('Could not insert PER data due to not logged in user.')

        body = json.loads(request.body.decode('utf-8'))

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            body['ip_address'] = x_forwarded_for.split(',')[-1].strip()
        else:
            body['ip_address'] = request.META.get('REMOTE_ADDR')

        required_fields = [
            'user_id',
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
        if 'user_id' not in body:
            body['user_id'] = None
        if 'country_id' not in body:
            body['country_id'] = None
        if 'ns' not in body:
            body['ns'] = None


        missing_fields = [field for field in required_fields if field not in body]
        if len(missing_fields):
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        if ' ' in body['code']:
            return bad_request('Code can not contain spaces, please choose a different one.')

        try:
            form = create_form(body)
        except:
            return bad_request('Could not insert PER form record.')

        if hasattr(form,'status_code') and form.status_code == 400:
            return bad_request('Could not insert PER form record due to inner failure.')

        if 'data' in body:
            for rubr in body['data']:
                try:
                    form_data = create_form_data(rubr, form)
                except:
                    return bad_request('Could not insert PER formdata record.')

                if hasattr(form_data,'status_code') and form_data.status_code == 400:
                    return bad_request('Could not insert PER form data record due to inner failure.')

        return JsonResponse({'status': 'ok'})


def change_form(raw):

    if 'id' not in raw:
        return bad_request('Id sending is mandatory')

    form = Form.objects.get(pk=int(raw['id']))  # If exists, get it

    if not form:
        return bad_request('Could not find PER form record.')

    #form.code         = raw['code']         # we do not change it
    #form.user_id      = raw['user_id']      # we do not change it
    form.name         = raw['name']         if 'name'         in raw else form.name
    form.language     = raw['language']     if 'language'     in raw else form.language
    form.country_id   = raw['country_id']   if 'country_id'   in raw else form.country_id
    form.ns           = raw['ns']           if 'ns'           in raw else form.ns
    form.ip_address   = raw['ip_address']   if 'ip_address'   in raw else form.ip_address
    form.started_at   = raw['started_at']   if 'started_at'   in raw else form.started_at
    form.ended_at     = raw['ended_at']     if 'ended_at'     in raw else form.ended_at
    form.submitted_at = raw['submitted_at'] if 'submitted_at' in raw else form.submitted_at
    form.comment      = raw['comment']      if 'comment'      in raw else form.comment
    form.validated    = raw['validated']    if 'validated'    in raw else form.validated
    form.finalized    = raw['finalized']    if 'finalized'    in raw else form.finalized
    form.save()

    return form

def change_form_data(raw, form):
    if 'form_id' not in raw:
        return bad_request('Form_id sending is mandatory')
    if 'id' not in raw:
        return bad_request('Question_id sending is mandatory')
    form_data = FormData.objects.filter(form_id=raw['form_id'], question_id=raw['id'])[0]  # If exists data item, get the first. We keep only 1 answer per question_id
    if not form_data:
        return bad_request('Could not find PER form data record.')

    #form_data.question_id     = raw['id'] # we do not change it
    form_data.selected_option = raw['op'] if 'op' in raw else form_data.selected_option
    form_data.notes           = raw['nt'] if 'nt' in raw else form_data.notes

    form_data.save()
    return form_data

class FormEdit(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):

        #if not request.user.is_authenticated:
        #    return bad_request('Could not insert PER data due to not logged in user.')

        body = json.loads(request.body.decode('utf-8'))

        required_fields = [
            'id',
        ]

        currentDT = datetime.datetime.now(pytz.timezone('UTC'))
        if 'ended_at' not in body:
            body['ended_at']     = str(currentDT)
        if 'submitted_at' not in body:
            body['submitted_at'] = str(currentDT)

        missing_fields = [field for field in required_fields if field not in body]
        if len(missing_fields):
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        try:
            form = change_form(body)
        except:
            return bad_request('Could not change PER form record.')

        if hasattr(form,'status_code') and form.status_code == 400:
            return bad_request('Could not change PER form record due to inner failure.')

        if 'data' in body:
            for rubr in body['data']:
                rubr['form_id'] = body['id']
                try:
                    form_data = change_form_data(rubr, form)
                except:
                    return bad_request('Could not change PER formdata record.')

                if hasattr(form_data,'status_code') and form_data.status_code == 400:
                    return bad_request('Could not change PER form data record due to inner failure.')

        return JsonResponse({'status': 'ok'})


class DraftSent(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):

        #if not request.user.is_authenticated:
        #    return bad_request('Could not insert PER data due to not logged in user.')

        body = json.loads(request.body.decode('utf-8'))

        required_fields = [
            'code', 'user_id',
        ]

        missing_fields = [field for field in required_fields if field not in body]
        if len(missing_fields):
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        if ' ' in body['code']:
            return bad_request('Code can not contain spaces, please choose a different one.')

        try:
            form = create_draft(body)
        except:
            return bad_request('Could not insert PER draft.')

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
#            "user_id": 1111,
#            "country_id": 47,
#            "ns": "Huhhhu vorikeri",
#            "data": [{"id": "1.1", "op": 3, "nt": "notes here"}, {"id": "1.2", "op": 0, "nt": "notes here also"}]
#             }' \
#  http://localhost:8000/sendperform
#  *** Afterpurger:
#  delete from per_formdata where notes like 'notes here%'; delete from per_form where name='Nemo';
