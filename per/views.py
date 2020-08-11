import json
import datetime
import pytz
import logging
from django.http import JsonResponse
from api.views import (
    bad_request,
    PublicJsonPostView,
)
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

from .models import (
    Draft, Form, FormData, WorkPlan, Overview
)

logger = logging.getLogger(__name__)


def create_draft(raw):
    Draft.objects.filter(
        code=raw['code'], country_id=raw['country_id'], user_id=raw['user_id']
    ).delete()  # If exists (a previous draft), delete it.
    draft = Draft.objects.create(
        code=raw['code'],
        country_id=raw['country_id'],
        user_id=raw['user_id'],
        data=raw['data'],
    )
    draft.save()
    return draft


def create_form(raw):
    form = Form.objects.create(
        code=raw['code'],
        name=raw['name'],
        language=raw['language'],
        user_id=raw['user_id'],
        country_id=raw['country_id'],
        ns=raw['ns'],
        ip_address=raw['ip_address'],
        started_at=raw['started_at'],
        ended_at=raw['ended_at'],
        submitted_at=raw['submitted_at'],
        comment=raw['comment'],
        validated=raw['validated'],
        finalized=raw['finalized'],
        # unique_id  = raw['unique_id'], # only KoBo form provided
    )
    form.save()
    return form


def create_form_data(raw, form):
    form_data = FormData.objects.create(
        form=form,
        question_id=raw['id'],
        selected_option=raw['op'],
        notes=raw['nt'],
    )
    form_data.save()
    return form_data


class FormSent(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        # if not request.user.is_authenticated:
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
            body['started_at'] = str(currentDT)
        if 'ended_at' not in body:
            body['ended_at'] = str(currentDT)
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
        except Exception:
            logger.error('Could not insert PER form record.', exc_info=True)
            return bad_request('Could not insert PER form record.')

        if hasattr(form, 'status_code') and form.status_code == 400:
            return bad_request('Could not insert PER form record due to inner failure.')

        if 'data' in body:
            for rubr in body['data']:
                try:
                    form_data = create_form_data(rubr, form)
                except Exception:
                    logger.error('Could not insert PER formdata record.', exc_info=True)
                    return bad_request('Could not insert PER formdata record.')

                if hasattr(form_data, 'status_code') and form_data.status_code == 400:
                    return bad_request('Could not insert PER form data record due to inner failure.')

        return JsonResponse({'status': 'ok'})


def change_form(raw):
    if 'id' not in raw:
        return bad_request('Id sending is mandatory')

    form = Form.objects.get(pk=int(raw['id']))  # If exists, get it

    if not form:
        return bad_request('Could not find PER form record.')

    # form.code = raw['code']         # we do not change it
    # form.user_id = raw['user_id']      # we do not change it
    form.name = raw.get('name', form.name)
    form.language = raw.get('language', form.language)
    form.country_id = raw.get('country_id', form.country_id)
    form.ns = raw.get('ns', form.ns)
    form.ip_address = raw.get('ip_address', form.ip_address)
    form.started_at = raw.get('started_at', form.started_at)
    form.ended_at = raw.get('ended_at', form.ended_at)
    form.submitted_at = raw.get('submitted_at', form.submitted_at)
    form.comment = raw.get('comment', form.comment)
    form.validated = raw.get('validated', form.validated)
    form.finalized = raw.get('finalized', form.finalized)
    form.save()
    return form


def change_form_data(raw, form):
    if 'form_id' not in raw:
        return bad_request('Form_id sending is mandatory')
    if 'id' not in raw:
        return bad_request('Question_id sending is mandatory')
    form_data = FormData.objects.filter(
        form_id=raw['form_id'], question_id=raw['id']
    )[0]  # If exists data item, get the first. We keep only 1 answer per question_id
    if not form_data:
        return bad_request('Could not find PER form data record.')

    # form_data.question_id     = raw['id'] # we do not change it
    form_data.selected_option = raw.get('op', form_data.selected_option)
    form_data.notes = raw.get('nt', form_data.notes)
    form_data.save()

    return form_data


class FormEdit(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        u = None
        richtokenstring = request.META.get('HTTP_AUTHORIZATION')
        if richtokenstring:
            try:
                receivedtoken = Token.objects.get(key=richtokenstring[6:])
            except Exception:
                logger.error('User token is not correct.', exc_info=True)
                return bad_request('User token is not correct.')
            u = User.objects.filter(is_active=True, pk=receivedtoken.user_id)
        else:
            return bad_request('User token is not given.')
        if not u:
            return bad_request('User is not logged in or inactive.')

        body = json.loads(request.body.decode('utf-8'))

        required_fields = [
            'id',
        ]

        currentDT = datetime.datetime.now(pytz.timezone('UTC'))
        if 'ended_at' not in body:
            body['ended_at'] = str(currentDT)
        if 'submitted_at' not in body:
            body['submitted_at'] = str(currentDT)

        missing_fields = [field for field in required_fields if field not in body]
        if len(missing_fields):
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        try:
            form = change_form(body)
        except Exception:
            logger.error('Could not change PER form record.', exc_info=True)
            return bad_request('Could not change PER form record.')

        if hasattr(form, 'status_code') and form.status_code == 400:
            return bad_request('Could not change PER form record due to inner failure.')

        if 'data' in body:
            for rubr in body['data']:
                rubr['form_id'] = body['id']
                try:
                    form_data = change_form_data(rubr, form)
                except Exception:
                    logger.error('Could not change PER formdata record.', exc_info=True)
                    return bad_request('Could not change PER formdata record.')

                if hasattr(form_data, 'status_code') and form_data.status_code == 400:
                    return bad_request('Could not change PER form data record due to inner failure.')

        return JsonResponse({'status': 'ok'})


class DraftSent(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        u = None
        richtokenstring = request.META.get('HTTP_AUTHORIZATION')
        if richtokenstring:
            try:
                receivedtoken = Token.objects.get(key=richtokenstring[6:])
            except Exception:
                logger.error('User token is not correct.', exc_info=True)
                return bad_request('User token is not correct.')

            u = User.objects.filter(is_active=True, pk=receivedtoken.user_id)
        else:
            return bad_request('User token is not given.')
        if not u:
            return bad_request('User is not logged in or inactive.')

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
            create_draft(body)
        except Exception:
            logger.error('User token is not correct.', exc_info=True)
            return bad_request('Could not insert PER draft.')

        return JsonResponse({'status': 'ok'})


def create_workplan(raw):
    # WorkPlan.objects.filter(code=raw['code'], user_id=raw['user_id']).delete()  # If exists (a previous WorkPlan), delete it.
    workplan = WorkPlan.objects.create(prioritization   = raw['prioritization'],
                                       components       = raw['components'],
                                       benchmark        = raw['benchmark'],
                                       actions          = raw['actions'],
                                       comments         = raw['comments'],
                                       timeline         = raw['timeline'] \
                                         if 'timeline' in raw else str(datetime.datetime.now(pytz.timezone('UTC'))),
                                       status           = raw['status'],
                                       support_required = raw['support_required'],
                                       focal_point      = raw['focal_point'],
                                       country_id       = raw['country_id'],
                                       code             = raw['code'],
                                       question_id      = raw['question_id'],
                                       user_id          = raw['user_id'],
                                       )
    workplan.save()
    return workplan

class WorkPlanSent(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        u = None
        richtokenstring = request.META.get('HTTP_AUTHORIZATION')
        if richtokenstring:
            try:
                receivedtoken = Token.objects.get(key=richtokenstring[6:])
            except:
                return bad_request('User token is not correct.')
            u = User.objects.filter(is_active=True, pk=receivedtoken.user_id)
        else:
            return bad_request('User token is not given.')
        if not u:
            return bad_request('User is not logged in or inactive.')

        body = json.loads(request.body.decode('utf-8'))

        required_fields = [
            'country_id', 'user_id',
        ]
        missing_fields = [field for field in required_fields if field not in body]
        if len(missing_fields):
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        if ' ' in body['question_id']:
            return bad_request('Question_id can not contain spaces, please choose a different one.')

        try:
            workplan = create_workplan(body)
        except:
            return bad_request('Could not insert PER WorkPlan.')

        return JsonResponse({'status': 'ok'})


def create_overview(raw):
    # Overview.objects.filter(code=raw['code'], user_id=raw['user_id']).delete()  # If exists (a previous Overview), delete it.
    overview = Overview.objects.create(country_id                           = raw['country_id'],
                                       user_id                              = raw['user_id'],
                                       date_of_current_capacity_assessment  = raw['date_of_current_capacity_assessment'] \
                                         if 'date_of_current_capacity_assessment' in raw else str(datetime.datetime.now(pytz.timezone('UTC'))),
                                       type_of_capacity_assessment          = raw['type_of_capacity_assessment'],
                                       branch_involved                      = raw['branch_involved'],
                                       focal_point_name                     = raw['focal_point_name'],
                                       focal_point_email                    = raw['focal_point_email'],
                                       had_previous_assessment              = raw['had_previous_assessment'],
                                       focus                                = raw['focus'],
                                       facilitated_by                       = raw['facilitated_by'],
                                       facilitator_email                    = raw['facilitator_email'],
                                       phone_number                         = raw['phone_number'],
                                       skype_address                        = raw['skype_address'],
                                       date_of_mid_term_review              = raw['date_of_mid_term_review'] \
                                         if 'date_of_mid_term_review' in raw else str(datetime.datetime.now(pytz.timezone('UTC'))),
                                       approximate_date_next_capacity_assmt = raw['approximate_date_next_capacity_assmt'] \
                                         if 'approximate_date_next_capacity_assmt' in raw else str(datetime.datetime.now(pytz.timezone('UTC'))),
                                       )

    overview.save()
    return overview

class OverviewSent(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        u = None
        richtokenstring = request.META.get('HTTP_AUTHORIZATION')
        if richtokenstring:
            try:
                receivedtoken = Token.objects.get(key=richtokenstring[6:])
            except:
                return bad_request('User token is not correct.')
            u = User.objects.filter(is_active=True, pk=receivedtoken.user_id)
        else:
            return bad_request('User token is not given.')
        if not u:
            return bad_request('User is not logged in or inactive.')

        body = json.loads(request.body.decode('utf-8'))

        required_fields = [
            'country_id', 'user_id',
        ]

        missing_fields = [field for field in required_fields if field not in body]
        if len(missing_fields):
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        try:
            overview = create_overview(body)
        except:
            return bad_request('Could not insert PER Overview.')

        return JsonResponse({'status': 'ok'})

def delete_workplan(raw):
    WorkPlan.objects.filter(id=raw['id']).delete()
    return

class DelWorkPlan(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        u = None
        richtokenstring = request.META.get('HTTP_AUTHORIZATION')
        if richtokenstring:
            try:
                receivedtoken = Token.objects.get(key=richtokenstring[6:])
            except:
                return bad_request('User token is not correct.')
            u = User.objects.filter(is_active=True, pk=receivedtoken.user_id)
            #origtoken = Token.objects.get_or_create(user=u)
        else:
            return bad_request('User token is not given.')
        if not u: # or receivedtoken.key != origtoken:
            return bad_request('User is not logged in or inactive.')

        # Did not work any of these...
        # if not request.user.is_authenticated:
        #   return bad_request('Could not insert PER data due to not logged in user.')
        # a = self.get_authenticated_user(self, request)
        # auth_header = request.META.get('HTTP_AUTHORIZATION')
        # parts = auth_header[6:].split(':')

        body = json.loads(request.body.decode('utf-8'))
        try:
            workplan = delete_workplan(body)
        except:
            return bad_request('Could not delete PER WorkPlan.')

        return JsonResponse({'status': 'ok'})

def delete_overview(raw):
    Overview.objects.filter(id=raw['id']).delete()
    return

class DelOverview(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        u = None
        richtokenstring = request.META.get('HTTP_AUTHORIZATION')
        if richtokenstring:
            try:
                receivedtoken = Token.objects.get(key=richtokenstring[6:])
            except:
                return bad_request('User token is not correct.')
            u = User.objects.filter(is_active=True, pk=receivedtoken.user_id)
        else:
            return bad_request('User token is not given.')
        if not u:
            return bad_request('User is not logged in or inactive.')

        body = json.loads(request.body.decode('utf-8'))

        try:
            workplan = delete_overview(body)
        except:
            return bad_request('Could not delete PER Overview.')

        return JsonResponse({'status': 'ok'})

def delete_draft(draftId):
    if draftId:
        Draft.objects.filter(id=draftId).delete()
    return

class DelDraft(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        u = None
        richtokenstring = request.META.get('HTTP_AUTHORIZATION')
        if richtokenstring:
            try:
                receivedtoken = Token.objects.get(key=richtokenstring[6:])
            except:
                return bad_request('User token is not correct.')
            u = User.objects.filter(is_active=True, pk=receivedtoken.user_id)
        else:
            return bad_request('User token is not given.')
        if not u:
            return bad_request('User is not logged in or inactive.')
        
        body = json.loads(request.body.decode('utf-8'))

        try:
            workplan = delete_draft(body['id'])
        except:
            return bad_request('Could not delete PER Draft.')
        
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
