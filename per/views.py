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
            form_data_in_db = FormData.objects.filter(form_id=form_id)

            with transaction.atomic():
                for qid in questions:
                    form_data = form_data_in_db.filter(question_id=qid).first()
                    if not form_data:
                        # Probably newly added question
                        try:
                            # TODO: look up bulk_save, (validation)
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

        assessment_number = request.data.get('assessment_number', None)
        branches_involved = request.data.get('branches_involved', None)
        country_id = request.data.get('country_id', None)
        date_of_assessment = request.data.get('date_of_assessment', None)
        date_of_mid_term_review = request.data.get('date_of_mid_term_review', None)
        date_of_next_asmt = request.data.get('date_of_next_asmt', None)
        facilitator_name = request.data.get('facilitator_name', None)
        facilitator_email = request.data.get('facilitator_email', None)
        facilitator_phone = request.data.get('facilitator_phone', None)
        facilitator_contact = request.data.get('facilitator_contact', None)
        is_epi = request.data.get('is_epi', False)
        method_asmt_used = request.data.get('method_asmt_used', None)
        ns_focal_point_name = request.data.get('ns_focal_point_name', None)
        ns_focal_point_email = request.data.get('ns_focal_point_email', None)
        ns_focal_point_phone = request.data.get('ns_focal_point_phone', None)
        other_consideration = request.data.get('other_consideration', None)
        partner_focal_point_name = request.data.get('partner_focal_point_name', None)
        partner_focal_point_email = request.data.get('partner_focal_point_email', None)
        partner_focal_point_phone = request.data.get('partner_focal_point_phone', None)
        partner_focal_point_organization = request.data.get('partner_focal_point_organization', None)
        type_of_assessment_id = request.data.get('type_of_assessment', None)
        user_id = request.data.get('user_id', None)

        try:
            overview = Overview.objects.create(
                assessment_number=assessment_number,  #TODO: logic to increase/handle
                branches_involved=branches_involved,
                country_id=country_id,
                date_of_assessment=date_of_assessment or None,
                date_of_mid_term_review=date_of_mid_term_review or None,
                date_of_next_asmt=date_of_next_asmt or None,
                facilitator_name=facilitator_name,
                facilitator_email=facilitator_email,
                facilitator_phone=facilitator_phone,
                facilitator_contact=facilitator_contact,
                is_epi=is_epi,
                is_finalized=False,  # We never want to finalize an Overview by start
                method_asmt_used=method_asmt_used,
                ns_focal_point_name=ns_focal_point_name,
                ns_focal_point_email=ns_focal_point_email,
                ns_focal_point_phone=ns_focal_point_phone,
                other_consideration=other_consideration,
                partner_focal_point_name=partner_focal_point_name,
                partner_focal_point_email=partner_focal_point_email,
                partner_focal_point_phone=partner_focal_point_phone,
                partner_focal_point_organization=partner_focal_point_organization,
                type_of_assessment_id=type_of_assessment_id,
                user_id=user_id
            )

            # For each Area create a Form record (Overview is the parent)
            areas = FormArea.objects.values_list('id', flat=True)
            form_data_to_create = []

            with transaction.atomic():
                for aid in areas:
                    form = Form.objects.create(
                        area_id=aid,
                        user_id=user_id,
                        overview_id=overview.id
                    )

                    # For each Question create a FormData record (Form is the parent)
                    questions = FormQuestion.objects.filter(component__area_id=aid).values_list('id', flat=True)
                    for qid in questions:
                        form_data_to_create.append(
                            FormData(
                                form=form,
                                question_id=qid
                            )
                        )
                FormData.objects.bulk_create(form_data_to_create)
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

        assessment_number = request.data.get('assessment_number', None)
        branches_involved = request.data.get('branches_involved', None)
        country_id = request.data.get('country_id', None)
        date_of_assessment = request.data.get('date_of_assessment', None)
        date_of_mid_term_review = request.data.get('date_of_mid_term_review', None)
        date_of_next_asmt = request.data.get('date_of_next_asmt', None)
        facilitator_name = request.data.get('facilitator_name', None)
        facilitator_email = request.data.get('facilitator_email', None)
        facilitator_phone = request.data.get('facilitator_phone', None)
        facilitator_contact = request.data.get('facilitator_contact', None)
        is_epi = request.data.get('is_epi', False)
        is_finalized = request.data.get('is_finalized', False)
        method_asmt_used = request.data.get('method_asmt_used', None)
        ns_focal_point_name = request.data.get('ns_focal_point_name', None)
        ns_focal_point_email = request.data.get('ns_focal_point_email', None)
        ns_focal_point_phone = request.data.get('ns_focal_point_phone', None)
        other_consideration = request.data.get('other_consideration', None)
        partner_focal_point_name = request.data.get('partner_focal_point_name', None)
        partner_focal_point_email = request.data.get('partner_focal_point_email', None)
        partner_focal_point_phone = request.data.get('partner_focal_point_phone', None)
        partner_focal_point_organization = request.data.get('partner_focal_point_organization', None)
        type_of_assessment_id = request.data.get('type_of_assessment', None)
        user_id = request.data.get('user_id', None)

        try:
            ov.assessment_number = assessment_number
            ov.branches_involved = branches_involved
            ov.country_id = country_id
            ov.date_of_assessment = date_of_assessment
            ov.date_of_mid_term_review = date_of_mid_term_review
            ov.date_of_next_asmt = date_of_next_asmt
            ov.facilitator_name = facilitator_name
            ov.facilitator_email = facilitator_email
            ov.facilitator_phone = facilitator_phone
            ov.facilitator_contact = facilitator_contact
            ov.is_epi = is_epi
            ov.is_finalized = is_finalized
            ov.method_asmt_used = method_asmt_used
            ov.ns_focal_point_name = ns_focal_point_name
            ov.ns_focal_point_email = ns_focal_point_email
            ov.ns_focal_point_phone = ns_focal_point_phone
            ov.other_consideration = other_consideration
            ov.partner_focal_point_name = partner_focal_point_name
            ov.partner_focal_point_email = partner_focal_point_email
            ov.partner_focal_point_phone = partner_focal_point_phone
            ov.partner_focal_point_organization = partner_focal_point_organization
            ov.type_of_assessment_id = type_of_assessment_id
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
