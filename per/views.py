import logging
from datetime import datetime, timezone

from django.db import transaction
from django.http import JsonResponse

from rest_framework import authentication, permissions
from rest_framework.views import APIView
from rest_framework import (
    views,
    viewsets,
    response,
    permissions,
    status,
    mixins,
    serializers,
)

from .models import (
    Form,
    FormData,
    WorkPlan,
    Overview,
    FormArea,
    FormQuestion,
)
from .admin_classes import RegionRestrictedAdmin
from api.views import bad_request
from api.models import Country

logger = logging.getLogger(__name__)


def get_now_str():
    return datetime.now(timezone.utc)


def parse_date(date_string):
    dateformat = "%Y-%m-%d"
    return datetime.strptime(date_string[:10], dateformat).replace(tzinfo=timezone.utc)


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
#                     )
#         except Exception:
#             logger.error('Could not insert PER formdata record.', exc_info=True)
#             return bad_request('Could not insert PER formdata record.')

#         return JsonResponse({'status': 'ok'})


class UpdatePerForm(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions

    def post(self, request):
        # Get the PER Form by ID
        form_id = request.data.get("id", None)
        if form_id is None:
            return bad_request("Could not complete request. Please include 'id' in the request.")
        form = Form.objects.filter(pk=form_id).first()
        if form is None:
            return bad_request("Could not find PER form record.")

        comment = request.data.get("comment", None)
        questions = request.data.get("questions", None)

        if questions is None:
            return bad_request("Questions are missing from the request.")

        # Check if the User has permissions to update
        if not request.user.is_superuser and not request.user.has_perm("api.per_core_admin"):
            countries, regions = self.get_request_user_regions(request)
            # These need to be strings
            if form.overview:
                ov_country = f"{form.overview.country.id}" or ""
                ov_region = f"{form.overview.country.region.id}" if form.overview.country.region else ""

                if ov_country not in countries and ov_region not in regions:
                    return bad_request("You don't have permission to update these forms.")
            else:
                return bad_request("You don't have permission to update these forms.")

        # Update the Form
        try:
            form.comment = comment
            form.save()
        except Exception:
            logger.error("Could not change PER form record.", exc_info=True)
            return bad_request("Could not change PER form record.")

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
                                selected_answer_id=questions[qid]["selected_answer"],
                                notes=questions[qid]["notes"]
                                # TODO: just as in the CreatePerForm
                            )
                        except Exception:
                            logger.error("Could not insert PER form record.", exc_info=True)
                            return bad_request("Could not insert PER form record.")
                    else:
                        if (
                            form_data.selected_answer_id != questions[qid]["selected_answer"]
                            or form_data.notes != questions[qid]["notes"]
                        ):
                            form_data.selected_answer_id = questions[qid]["selected_answer"] or form_data.selected_answer_id
                            form_data.notes = questions[qid]["notes"] or form_data.notes
                            form_data.save()
        except Exception:
            logger.error("Could not change PER formdata record.", exc_info=True)
            return bad_request("Could not change PER formdata record.")

        return JsonResponse({"status": "ok", "overview_id": form.overview_id})


class UpdatePerForms(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions

    def post(self, request):
        forms = request.data.get("forms", None)
        forms_data = request.data.get("forms_data", None)

        overview_id = forms[list(forms.keys())[0]]["overview"]["id"]
        ov = Overview.objects.filter(id=overview_id).first()

        if not forms or not forms_data:
            return bad_request("Could not complete request. 'forms' or 'forms_data' are missing.")

        # Check if the User has permissions to update
        if not request.user.is_superuser and not request.user.has_perm("api.per_core_admin"):
            countries, regions = self.get_request_user_regions(request)

            if ov:
                # These need to be strings
                ov_country = f"{ov.country.id}" or ""
                ov_region = f"{ov.country.region.id}" if ov.country.region else ""

                if ov_country not in countries and ov_region not in regions:
                    return bad_request("You don't have permission to update these forms.")
            else:
                return bad_request("You don't have permission to update these forms.")

        # # Update the Forms
        try:
            with transaction.atomic():
                for form_id in forms:
                    form = Form.objects.filter(pk=forms[form_id].get("id")).first()
                    if form:
                        form.comment = forms[form_id].get("comment")
                        form.save()
        except Exception:
            logger.error("Could not update PER Forms.", exc_info=True)
            return bad_request("Could not update PER Forms.")

        # Update the FormsData
        try:
            with transaction.atomic():
                for fid in forms_data:
                    # All FormData related to the Form
                    db_form_data = FormData.objects.filter(form_id=fid)
                    form_data_to_update = []
                    for qid in forms_data[fid]:
                        db_fd = db_form_data.filter(question_id=qid).first()
                        selected_answer = forms_data[fid][qid].get("selected_answer", None)
                        notes = forms_data[fid][qid].get("notes", None)

                        if selected_answer:
                            selected_answer = int(selected_answer)

                        if not db_fd:
                            # Missing question
                            FormData.objects.create(
                                form_id=fid, question_id=qid, selected_answer_id=selected_answer, notes=notes
                            )
                        else:
                            if db_fd.selected_answer_id == selected_answer and db_fd.notes == notes:
                                continue
                            db_fd.selected_answer_id = selected_answer
                            db_fd.notes = notes
                            form_data_to_update.append(db_fd)
                    FormData.objects.bulk_update(form_data_to_update, ["selected_answer_id", "notes"])
        except Exception:
            logger.error("Could not update PER FormsData.", exc_info=True)
            return bad_request("Could not update PER FormsData.")

        return JsonResponse({"status": "ok"})


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
        required_fields = ("country_id", "user_id")
        missing_fields = [field for field in required_fields if field not in request.data]
        if missing_fields:
            return bad_request("Could not complete request. Please submit %s" % ", ".join(missing_fields))

        question_id = request.data.get("question_id", None)
        if " " in question_id:
            return bad_request("Question ID can not contain spaces.")

        prioritization = request.data.get("prioritization", None)
        components = request.data.get("components", None)
        benchmark = request.data.get("benchmark", None)
        actions = request.data.get("actions", None)
        comments = request.data.get("comments", None)
        timeline = request.data.get("timeline", get_now_str())
        status = request.data.get("status", None)
        support_required = request.data.get("support_required", None)
        focal_point = request.data.get("focal_point", None)
        country_id = request.data.get("country_id", None)
        code = request.data.get("code", None)
        user_id = request.data.get("user_id", None)

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
                user_id=user_id,
            )
        except Exception:
            return bad_request("Could not insert PER WorkPlan.")

        return JsonResponse({"status": "ok"})


class CreatePerOverview(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions

    def post(self, request):
        required_fields = ("date_of_assessment", "type_of_assessment", "country_id", "user_id")
        missing_fields = [field for field in required_fields if field not in request.data or not request.data[field]]
        if missing_fields:
            return bad_request("Could not complete request. Please submit %s" % ", ".join(missing_fields))

        assessment_number = request.data.get("assessment_number", None)
        branches_involved = request.data.get("branches_involved", None)
        country_id = request.data.get("country_id", None)
        date_of_assessment = request.data.get("date_of_assessment", None)
        date_of_mid_term_review = request.data.get("date_of_mid_term_review", None)
        date_of_next_asmt = request.data.get("date_of_next_asmt", None)
        facilitator_name = request.data.get("facilitator_name", None)
        facilitator_email = request.data.get("facilitator_email", None)
        facilitator_phone = request.data.get("facilitator_phone", None)
        facilitator_contact = request.data.get("facilitator_contact", None)
        is_epi = request.data.get("is_epi", False)
        method_asmt_used = request.data.get("method_asmt_used", None)
        ns_focal_point_name = request.data.get("ns_focal_point_name", None)
        ns_focal_point_email = request.data.get("ns_focal_point_email", None)
        ns_focal_point_phone = request.data.get("ns_focal_point_phone", None)
        other_consideration = request.data.get("other_consideration", None)
        partner_focal_point_name = request.data.get("partner_focal_point_name", None)
        partner_focal_point_email = request.data.get("partner_focal_point_email", None)
        partner_focal_point_phone = request.data.get("partner_focal_point_phone", None)
        partner_focal_point_organization = request.data.get("partner_focal_point_organization", None)
        type_of_assessment_id = request.data.get("type_of_assessment", None)
        user_id = request.data.get("user_id", None)

        # Check if the User has permissions to create
        if not request.user.is_superuser and not request.user.has_perm("api.per_core_admin"):
            countries, regions = self.get_request_user_regions(request)
            country = Country.objects.filter(id=country_id).first() if country_id else None
            if country:
                # These need to be strings
                country_id_string = f"{country.id}" or ""
                region_id_string = f"{country.region.id}" if country.region else ""

                if country_id_string not in countries and region_id_string not in regions:
                    return bad_request("You don't have permission to create an Overview for the selected Country.")
            else:
                return bad_request("You don't have permission to create an Overview for the selected Country.")

        prevOverview = Overview.objects.filter(country_id=country_id).order_by("-created_at").first()
        prevOverview_assessmentNumber = prevOverview.assessment_number + 1 if prevOverview else 1

        try:
            overview = Overview.objects.create(
                assessment_number=assessment_number if assessment_number else prevOverview_assessmentNumber,
                branches_involved=branches_involved,
                country_id=country_id,
                date_of_assessment=parse_date(date_of_assessment) if date_of_assessment else None,
                date_of_mid_term_review=parse_date(date_of_mid_term_review) if date_of_mid_term_review else None,
                date_of_next_asmt=parse_date(date_of_next_asmt) if date_of_next_asmt else None,
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
                user_id=user_id,
            )

            # For each Area create a Form record (Overview is the parent)
            areas = FormArea.objects.values_list("id", flat=True)
            form_data_to_create = []

            with transaction.atomic():
                for aid in areas:
                    form = Form.objects.create(area_id=aid, user_id=user_id, overview_id=overview.id)

                    # For each Question create a FormData record (Form is the parent)
                    questions = FormQuestion.objects.filter(component__area_id=aid).values_list("id", flat=True)
                    for qid in questions:
                        form_data_to_create.append(FormData(form=form, question_id=qid))
                FormData.objects.bulk_create(form_data_to_create)
        except Exception:
            return bad_request("Could not create PER Assessment.")

        return JsonResponse({"status": "ok", "overview_id": overview.id})


class UpdatePerOverview(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)
    get_request_user_regions = RegionRestrictedAdmin.get_request_user_regions

    def post(self, request):
        id = request.data.get("id", None)
        if id is None:
            return bad_request("Could not complete request. Please submit include id")
        ov = Overview.objects.filter(pk=id).first()
        if ov is None:
            return bad_request("Could not find PER Overview form record.")
        required_fields = ("date_of_assessment", "type_of_assessment", "country_id", "user_id")
        missing_fields = [field for field in required_fields if field not in request.data or not request.data[field]]
        if missing_fields:
            return bad_request("Could not complete request. Please submit %s" % ", ".join(missing_fields))

        # Fool-proofing so one couldn't change the Overview data even through
        # plain API requests, if it's finalized already
        if ov.is_finalized:
            return bad_request("Form is already finalized. Can't save any changes to it.")

        assessment_number = request.data.get("assessment_number", None)
        branches_involved = request.data.get("branches_involved", None)
        country_id = request.data.get("country_id", None)
        date_of_assessment = request.data.get("date_of_assessment", None)
        date_of_mid_term_review = request.data.get("date_of_mid_term_review", None)
        date_of_next_asmt = request.data.get("date_of_next_asmt", None)
        facilitator_name = request.data.get("facilitator_name", None)
        facilitator_email = request.data.get("facilitator_email", None)
        facilitator_phone = request.data.get("facilitator_phone", None)
        facilitator_contact = request.data.get("facilitator_contact", None)
        is_epi = request.data.get("is_epi", False)
        is_finalized = request.data.get("is_finalized", False)
        method_asmt_used = request.data.get("method_asmt_used", None)
        ns_focal_point_name = request.data.get("ns_focal_point_name", None)
        ns_focal_point_email = request.data.get("ns_focal_point_email", None)
        ns_focal_point_phone = request.data.get("ns_focal_point_phone", None)
        other_consideration = request.data.get("other_consideration", None)
        partner_focal_point_name = request.data.get("partner_focal_point_name", None)
        partner_focal_point_email = request.data.get("partner_focal_point_email", None)
        partner_focal_point_phone = request.data.get("partner_focal_point_phone", None)
        partner_focal_point_organization = request.data.get("partner_focal_point_organization", None)
        type_of_assessment_id = request.data.get("type_of_assessment", None)
        user_id = request.data.get("user_id", None)

        # Check if the User has permissions to update
        if not request.user.is_superuser and not request.user.has_perm("api.per_core_admin"):
            countries, regions = self.get_request_user_regions(request)
            country = Country.objects.filter(id=country_id).first() if country_id else None
            if country:
                # These need to be strings
                country_id_string = f"{country.id}" or ""
                region_id_string = f"{country.region.id}" if country.region else ""

                if country_id_string not in countries and region_id_string not in regions:
                    return bad_request("You don't have permission to update the Overview for the selected Country.")
            else:
                return bad_request("You don't have permission to update the Overview for the selected Country.")

        # prev_overview = None
        # if ov.country_id != country_id:
        #     prev_overview = Overview.objects.filter(country_id=country_id).order_by('-created_at').first()

        try:
            # if prev_overview:
            #     ov.assessment_number = prev_overview.assessment_number + 1
            ov.assessment_number = assessment_number
            ov.branches_involved = branches_involved
            ov.country_id = country_id
            ov.date_of_assessment = parse_date(date_of_assessment) if date_of_assessment else None
            ov.date_of_mid_term_review = parse_date(date_of_mid_term_review) if date_of_mid_term_review else None
            ov.date_of_next_asmt = parse_date(date_of_next_asmt) if date_of_next_asmt else None
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
            logger.error("Could not change PER Overview form record.", exc_info=True)
            return bad_request("Could not change PER Overview form record.")

        return JsonResponse({"status": "ok", "is_finalized": ov.is_finalized})


class DeletePerOverview(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        overview_id = request.data.get("id", None)
        if overview_id is None:
            return bad_request("Need to provide Overview ID.")

        try:
            ov = Overview.objects.filter(id=overview_id, user=user, is_finalized=False).first()
            if ov:
                ov.delete()
            else:
                return bad_request(f"Overview with the ID: {overview_id} is finalized or not created by your user.")
        except Exception:
            return bad_request("Could not delete PER Overview.")

        return JsonResponse({"status": "ok"})


class DelWorkPlan(APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        workplan_id = request.data.get("id", None)
        if workplan_id is None:
            return bad_request("Need to provide WorkPlan ID.")

        try:
            WorkPlan.objects.filter(id=workplan_id).delete()
        except Exception:
            return bad_request("Could not delete PER WorkPlan.")

        return JsonResponse({"status": "ok"})
