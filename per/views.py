import logging
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from .models import (
    Form, FormData, WorkPlan, Overview
)
from api.views import bad_request

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """ https://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_now_str():
    return str(timezone.now())


# TODO: REWRITE MOST VIEWS
class FormSent(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        required_fields = [
            'user_id',
            'code',
            'name',
            'language',
        ]

        missing_fields = [field for field in required_fields if field not in request.data]
        if len(missing_fields):
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        name = request.data.get('name', None)
        code = request.data.get('code', None)
        language = request.data.get('language', None)
        comment = request.data.get('comment', None)
        is_validated = request.data.get('is_validated', False)
        is_finalized = request.data.get('is_finalized', False)
        user_id = comment = request.data.get('user_id', None)
        country_id = request.data.get('country_id', None)
        ns = request.data.get('ns', None)
        data = request.data.get('data', None)

        if ' ' in code:
            return bad_request('Code can not contain spaces, please choose a different one.')

        # Create the Form object
        try:
            form = Form.objects.create(
                code=code,
                name=name,
                language=language,
                user_id=user_id,
                country_id=country_id,
                ns=ns,
                comment=comment,
                is_validated=is_validated,
                is_finalized=is_finalized
            )
        except Exception:
            logger.error('Could not insert PER form record.', exc_info=True)
            return bad_request('Could not insert PER form record.')

        # Create FormData of the Form
        if data:
            try:
                with transaction.atomic():  # all or nothing
                    for rubr in data:
                        FormData.objects.create(form=form,
                                                question_id=rubr['id'],
                                                selected_option=rubr['op'],
                                                notes=rubr['nt'])
            except Exception:
                logger.error('Could not insert PER formdata record.', exc_info=True)
                return bad_request('Could not insert PER formdata record.')

        return JsonResponse({'status': 'ok'})


class FormEdit(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        form_id = request.data.get('id', None)
        if form_id is None:
            return bad_request('Could not complete request. Please submit %s' % form_id)

        form = Form.objects.filter(pk=form_id).first()
        if form is None:
            return bad_request('Could not find PER form record.')

        name = request.data.get('name', form.name)
        language = request.data.get('language', form.language)
        country_id = request.data.get('country_id', form.country_id)
        ns = request.data.get('ns', form.ns)
        comment = request.data.get('comment', form.comment)
        is_validated = request.data.get('is_validated', form.is_validated)
        is_finalized = request.data.get('is_finalized', form.is_finalized)
        data = request.data.get('data', None)

        # Update the Form properties and try to save
        try:
            form.name = name
            form.language = language
            form.country_id = country_id
            form.ns = ns
            form.comment = comment
            form.is_validated = is_validated
            form.is_finalized = is_finalized
            form.save()
        except Exception:
            logger.error('Could not change PER form record.', exc_info=True)
            return bad_request('Could not change PER form record.')

        # Update Form Data of the Form
        if data:
            try:
                with transaction.atomic():  # all or nothing
                    for rubr in data:
                        if rubr['id'] is None:
                            raise Exception('PER Form Data ID was missing. Form ID: {}'.format(form_id))

                        form_data = FormData.objects.filter(form_id=form_id, question_id=rubr['id']).first()
                        if not form_data:
                            raise Exception('Could not find PER Form Data record. \
                                            Form ID: {} Form Data ID: {}'.format(form_id, rubr['id']))

                        form_data.selected_option = rubr['op'] if rubr['op'] else form_data.selected_option
                        form_data.notes = rubr['nt'] if rubr['nt'] else form_data.notes

                        form_data.save()
            except Exception as err:
                logger.error('Could not change PER formdata record.', exc_info=True)
                return bad_request('Could not change PER formdata record. {}'.format(err))

        return JsonResponse({'status': 'ok'})


class WorkPlanSent(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        required_fields = ('country_id', 'user_id')
        missing_fields = [field for field in required_fields if field not in request.data]
        if missing_fields:
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        question_id = request.data.get('question_id', None)
        if ' ' in question_id:
            return bad_request('Question ID can not contain spaces.')

        prioritization = request.data.get('prioritization', None)
        components = request.data.get('components', None)
        benchmark = request.data.get('benchmark', None)
        actions = request.data.get('actions', None)
        comments = request.data.get('comments', None)
        timeline = request.data.get('timeline', get_now_str())
        status = request.data.get('status', None)
        support_required = request.data.get('support_required', None)
        focal_point = request.data.get('focal_point', None)
        country_id = request.data.get('country_id', None)
        code = request.data.get('code', None)
        user_id = request.data.get('user_id', None)

        try:
            WorkPlan.objects.create(
                prioritization=prioritization,
                components=components,
                benchmark=benchmark,
                actions=actions,
                comments=comments,
                timeline=timeline,
                status=status,
                support_required=support_required,
                focal_point=focal_point,
                country_id=country_id,
                code=code,
                question_id=question_id,
                user_id=user_id
            )
        except Exception:
            return bad_request('Could not insert PER WorkPlan.')

        return JsonResponse({'status': 'ok'})


class OverviewSent(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        required_fields = ('country_id', 'user_id')
        missing_fields = [field for field in required_fields if field not in request.data]
        if missing_fields:
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        country_id = request.data.get('country_id', None)
        user_id = request.data.get('user_id', None)
        country_id = request.data.get('country_id', None)
        date_of_current_capacity_assessment = request.data.get('date_of_current_capacity_assessment', get_now_str())
        type_of_capacity_assessment = request.data.get('type_of_capacity_assessment', None)
        branch_involved = request.data.get('branch_involved', None)
        focal_point_name = request.data.get('focal_point_name', None)
        focal_point_email = request.data.get('focal_point_email', None)
        had_previous_assessment = request.data.get('had_previous_assessment', None)
        focus = request.data.get('focus', None)
        facilitated_by = request.data.get('facilitated_by', None)
        facilitator_email = request.data.get('facilitator_email', None)
        phone_number = request.data.get('phone_number', None)
        skype_address = request.data.get('skype_address', None)
        date_of_mid_term_review = request.data.get('date_of_mid_term_review', get_now_str())
        approximate_date_next_capacity_assmt = request.data.get('approximate_date_next_capacity_assmt', get_now_str())

        try:
            Overview.objects.create(
                country_id=country_id,
                user_id=user_id,
                date_of_current_capacity_assessment=date_of_current_capacity_assessment,
                type_of_capacity_assessment=type_of_capacity_assessment,
                branch_involved=branch_involved,
                focal_point_name=focal_point_name,
                focal_point_email=focal_point_email,
                had_previous_assessment=had_previous_assessment,
                focus=focus,
                facilitated_by=facilitated_by,
                facilitator_email=facilitator_email,
                phone_number=phone_number,
                skype_address=skype_address,
                date_of_mid_term_review=date_of_mid_term_review,
                approximate_date_next_capacity_assmt=approximate_date_next_capacity_assmt
            )
        except Exception:
            return bad_request('Could not insert PER Overview.')

        return JsonResponse({'status': 'ok'})


class DelWorkPlan(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        workplan_id = request.data.get('id', None)
        if workplan_id is None:
            return bad_request('Need to provide WorkPlan ID.')

        try:
            WorkPlan.objects.filter(id=workplan_id).delete()
        except Exception:
            return bad_request('Could not delete PER WorkPlan.')

        return JsonResponse({'status': 'ok'})


class DelOverview(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        overview_id = request.data.get('id', None)
        if overview_id is None:
            return bad_request('Need to provide Overview ID.')

        try:
            Overview.objects.filter(id=overview_id).delete()
        except Exception:
            return bad_request('Could not delete PER Overview.')

        return JsonResponse({'status': 'ok'})
