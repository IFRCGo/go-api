import logging
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from .models import (
    Form, FormData, WorkPlan, Overview, FormArea, FormQuestion
)
from api.views import bad_request

logger = logging.getLogger(__name__)


def get_now_str():
    return str(timezone.now())


# class CreatePerForm(APIView):
#     authentication_classes = (authentication.TokenAuthentication,)
#     permissions_classes = (permissions.IsAuthenticated,)

#     def post(self, request):
#         area_id = request.data.get('area_id', None)
#         comment = request.data.get('comment', None)
#         overview_id = request.data.get('overview_id', None)
#         questions = request.data.get('questions', None)
#         user_id = request.data.get('user_id', None)

#         if questions is None:
#             return bad_request('Questions are missing from the request.')

#         try:
#             form = Form.objects.create(
#                 area_id=area_id,
#                 user_id=user_id,
#                 comment=comment,
#                 overview_id=overview_id
#             )
#         except Exception:
#             logger.error('Could not insert PER form record.', exc_info=True)
#             return bad_request('Could not insert PER form record.')

#         # Create FormData of the Form
#         try:
#             with transaction.atomic():  # all or nothing
#                 for qid in questions:
#                     FormData.objects.create(
#                         form=form,
#                         question_id=qid,
#                         selected_answer_id=questions[qid]['selected_answer'],
#                         notes=questions[qid]['notes']
#                         # TODO: check if FormData also needs is_epi and is_benchmark flags
#                     )
#         except Exception:
#             logger.error('Could not insert PER formdata record.', exc_info=True)
#             return bad_request('Could not insert PER formdata record.')

#         return JsonResponse({'status': 'ok'})


class UpdatePerForm(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        # Get the PER Form by ID
        form_id = request.data.get('id', None)
        if form_id is None:
            return bad_request('Could not complete request. Please submit include id')
        form = Form.objects.filter(pk=form_id).first()
        if form is None:
            return bad_request('Could not find PER form record.')

        comment = request.data.get('comment', None)
        questions = request.data.get('questions', None)

        if questions is None:
            return bad_request('Questions are missing from the request.')

        # Update the Form
        try:
            form.comment = comment
            form.save()
        except Exception:
            logger.error('Could not change PER form record.', exc_info=True)
            return bad_request('Could not change PER form record.')

        # Update the FormData
        try:
            # TODO: Maybe it would be faster to get all the questions with ONE query and
            # loop that matching with the questions array, instead of having a
            # query every loop (?)
            for qid in questions:
                form_data = FormData.objects.filter(form_id=form_id, question_id=qid).first()
                if not form_data:
                    # Probably newly added question
                    try:
                        form_data = FormData.objects.create(
                            form=form,
                            question_id=qid,
                            selected_answer_id=questions[qid]['selected_answer'],
                            notes=questions[qid]['notes']
                            # TODO: just as in the CreatePerForm
                        )
                    except Exception:
                        logger.error('Could not insert PER form record.', exc_info=True)
                        return bad_request('Could not insert PER form record.')
                else:
                    if form_data.selected_answer_id != questions[qid]['selected_answer'] \
                            or form_data.notes != questions[qid]['notes']:
                        form_data.selected_answer_id = questions[qid]['selected_answer'] or form_data.selected_answer_id
                        form_data.notes = questions[qid]['notes'] or form_data.notes
                        form_data.save()
        except Exception:
            logger.error('Could not change PER formdata record.', exc_info=True)
            return bad_request('Could not change PER formdata record.')

        return JsonResponse({'status': 'ok', 'overview_id': form.overview_id})


# # For now, a Form can only be deleted if it's parent Overview is deleted
# class DeletePerForm(APIView):
#     authentication_classes = (authentication.TokenAuthentication,)
#     permissions_classes = (permissions.IsAuthenticated,)

#     def post(self, request):
#         user = request.user
#         form_id = request.data.get('id', None)
#         if form_id is None:
#             return bad_request('Need to provide Form ID.')

#         try:
#             # Also deletes FormData since CASCADE fk
#             # TODO: check for is_finalized of Overview maybe?
#             Form.objects.filter(id=form_id, user=user).delete()
#         except Exception:
#             return bad_request('Could not delete PER Form.')

#         return JsonResponse({'status': 'ok'})


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


class CreatePerOverview(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        required_fields = ('country_id', 'user_id')
        missing_fields = [field for field in required_fields if field not in request.data]
        if missing_fields:
            return bad_request('Could not complete request. Please submit %s' % ', '.join(missing_fields))

        approximate_date_next_capacity_assmt = request.data.get('approximate_date_next_capacity_assmt', None)
        branch_involved = request.data.get('branch_involved', None)
        country_id = request.data.get('country_id', None)
        date_of_current_capacity_assessment = request.data.get('date_of_current_capacity_assessment', None)
        date_of_last_capacity_assessment = request.data.get('date_of_last_capacity_assessment', None)
        date_of_mid_term_review = request.data.get('date_of_mid_term_review', None)
        facilitated_by = request.data.get('facilitated_by', None)
        facilitator_email = request.data.get('facilitator_email', None)
        focus = request.data.get('focus', None)
        focal_point_name = request.data.get('focal_point_name', None)
        focal_point_email = request.data.get('focal_point_email', None)
        had_previous_assessment = request.data.get('had_previous_assessment', None)
        phone_number = request.data.get('phone_number', None)
        skype_address = request.data.get('skype_address', None)
        type_of_ca_id = request.data.get('type_of_ca', None)
        user_id = request.data.get('user_id', None)

        try:
            overview = Overview.objects.create(
                approximate_date_next_capacity_assmt=approximate_date_next_capacity_assmt or None,
                branch_involved=branch_involved,
                country_id=country_id,
                date_of_current_capacity_assessment=date_of_current_capacity_assessment or None,
                date_of_last_capacity_assessment=date_of_last_capacity_assessment or None,
                date_of_mid_term_review=date_of_mid_term_review or None,
                facilitated_by=facilitated_by,
                facilitator_email=facilitator_email,
                focal_point_name=focal_point_name,
                focal_point_email=focal_point_email,
                focus=focus,
                had_previous_assessment=had_previous_assessment,
                is_finalized=False,
                phone_number=phone_number,
                skype_address=skype_address,
                type_of_ca_id=type_of_ca_id,
                user_id=user_id
            )

            areas = FormArea.objects.values_list('id', flat=True)
            for aid in areas:
                form = Form.objects.create(
                    area_id=aid,
                    user_id=user_id,
                    overview_id=overview.id
                )
                questions = FormQuestion.objects.filter(component__area_id=aid).values_list('id', flat=True)
                for qid in questions:
                    FormData.objects.create(
                        form=form,
                        question_id=qid,
                    )
        except Exception:
            return bad_request('Could not create PER Assessment.')

        return JsonResponse({'status': 'ok', 'overview_id': overview.id})


class UpdatePerOverview(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        id = request.data.get('id', None)
        if id is None:
            return bad_request('Could not complete request. Please submit include id')
        ov = Overview.objects.filter(pk=id).first()
        if ov is None:
            return bad_request('Could not find PER Overview form record.')

        approximate_date_next_capacity_assmt = request.data.get('approximate_date_next_capacity_assmt', None)
        branch_involved = request.data.get('branch_involved', None)
        country_id = request.data.get('country_id', None)
        date_of_current_capacity_assessment = request.data.get('date_of_current_capacity_assessment', None)
        date_of_last_capacity_assessment = request.data.get('date_of_last_capacity_assessment', None)
        date_of_mid_term_review = request.data.get('date_of_mid_term_review', None)
        facilitated_by = request.data.get('facilitated_by', None)
        facilitator_email = request.data.get('facilitator_email', None)
        focus = request.data.get('focus', None)
        focal_point_name = request.data.get('focal_point_name', None)
        focal_point_email = request.data.get('focal_point_email', None)
        had_previous_assessment = request.data.get('had_previous_assessment', None)
        is_finalized = request.data.get('is_finalized', False)
        phone_number = request.data.get('phone_number', None)
        skype_address = request.data.get('skype_address', None)
        type_of_ca_id = request.data.get('type_of_ca', None)
        user_id = request.data.get('user_id', None)

        try:
            ov.approximate_date_next_capacity_assmt = approximate_date_next_capacity_assmt
            ov.branch_involved = branch_involved
            ov.country_id = country_id
            ov.date_of_current_capacity_assessment = date_of_current_capacity_assessment
            ov.date_of_last_capacity_assessment = date_of_last_capacity_assessment
            ov.date_of_mid_term_review = date_of_mid_term_review
            ov.facilitated_by = facilitated_by
            ov.facilitator_email = facilitator_email
            ov.focus = focus
            ov.focal_point_email = focal_point_email
            ov.focal_point_name = focal_point_name
            ov.had_previous_assessment = had_previous_assessment
            ov.is_finalized = is_finalized
            ov.phone_number = phone_number
            ov.skype_address = skype_address
            ov.type_of_ca_id = type_of_ca_id
            ov.user_id = user_id
            ov.save()
        except Exception:
            logger.error('Could not change PER Overview form record.', exc_info=True)
            return bad_request('Could not change PER Overview form record.')

        return JsonResponse({'status': 'ok'})


class DeletePerOverview(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        overview_id = request.data.get('id', None)
        if overview_id is None:
            return bad_request('Need to provide Overview ID.')

        try:
            Overview.objects.filter(id=overview_id, user=user, is_finalized=False).delete()
        except Exception:
            return bad_request('Could not delete PER Overview.')

        # TODO: check if all connected Forms are deleted or need to delete manually (should cascade)

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

