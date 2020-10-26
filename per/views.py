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


def create_form_object(aid, lang, uid, cid, comm, is_draft, is_val, is_fin):
    form = Form.objects.create(
        area_id=aid,
        language=lang,  # FIXME: this is probably not needed? defaulting to english
        user_id=uid,
        country_id=cid,
        comment=comm,
        is_draft=is_draft,
        is_validated=is_val,
        is_finalized=is_fin
    )
    return form


class CreatePerForm(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        area_id = request.data.get('area_id', None)
        user_id = request.data.get('user_id', None)
        country_id = request.data.get('country_id', None)
        is_draft = request.data.get('is_draft', None)
        is_finalized = request.data.get('is_finalized', False)  # FIXME: never seem to be used anywhere
        is_validated = request.data.get('is_validated', False)  # FIXME: never seem to be used anywhere
        comment = request.data.get('comment', None)  # FIXME: never seem to be used anywhere
        questions = request.data.get('questions', None)

        if questions is None:
            return bad_request('Questions are missing from the request.')

        try:
            form = create_form_object(area_id, 2, user_id, country_id, comment, is_draft, is_validated, is_finalized)
        except Exception:
            logger.error('Could not insert PER form record.', exc_info=True)
            return bad_request('Could not insert PER form record.')

        # Create FormData of the Form
        try:
            with transaction.atomic():  # all or nothing
                for qid in questions:
                    FormData.objects.create(
                        form=form,
                        question_id=qid,
                        selected_answer_id=questions[qid]['selectedAnswer'],
                        notes=questions[qid]['notes']
                    )
        except Exception:
            logger.error('Could not insert PER formdata record.', exc_info=True)
            return bad_request('Could not insert PER formdata record.')

        return JsonResponse({'status': 'ok'})


class EditPerForm(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        # Get the PER Form by ID
        form_id = request.data.get('id', None)
        if form_id is None:
            return bad_request(f'Could not complete request. Please submit {form_id}')
        form = Form.objects.filter(pk=form_id).first()
        if form is None:
            return bad_request('Could not find PER form record.')

        area_id = request.data.get('area_id', None)
        user_id = request.data.get('user_id', None)
        country_id = request.data.get('country_id', None)
        is_draft = request.data.get('is_draft', None)
        is_finalized = request.data.get('is_finalized', False)  # FIXME: never seem to be used anywhere
        is_validated = request.data.get('is_validated', False)  # FIXME: never seem to be used anywhere
        comment = request.data.get('comment', None)  # FIXME: never seem to be used anywhere
        questions = request.data.get('questions', None)

        if questions is None:
            return bad_request('Questions are missing from the request.')

        # Update the Form
        try:
            form.area_id = area_id
            form.country_id = country_id
            form.comment = comment
            form.is_draft = is_draft
            form.is_finalized = is_finalized
            form.is_validated = is_validated
            form.save()
        except Exception:
            logger.error('Could not change PER form record.', exc_info=True)
            return bad_request('Could not change PER form record.')

        # Update the FormData
        try:
            with transaction.atomic():  # all or nothing
                for qid in questions:
                    form_data = FormData.objects.filter(form_id=form_id, question_id=qid).first()
                    # Probably newly added question
                    if not form_data:
                        try:
                            form = create_form_object(
                                area_id, 2, user_id, country_id, comment, is_draft, is_validated, is_finalized
                            )
                        except Exception:
                            logger.error('Could not insert PER form record.', exc_info=True)
                            return bad_request('Could not insert PER form record.')

                    form_data.selected_answer_id = questions[qid]['selectedAnswer'] or form_data.selected_answer_id
                    form_data.notes = questions[qid]['notes'] or form_data.notes
                    form_data.save()
        except Exception:
            logger.error('Could not change PER formdata record.', exc_info=True)
            return bad_request('Could not change PER formdata record.')

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
