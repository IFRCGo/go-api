import os
import datetime

from django.utils.translation import gettext
from django.db import models, transaction
from django.conf import settings
from django.contrib.auth.models import User


from rest_framework import serializers

from lang.serializers import ModelSerializer
from main.writable_nested_serializers import NestedCreateMixin, NestedUpdateMixin
from api.serializers import UserNameSerializer, DisasterTypeSerializer, MiniDistrictSerializer, MiniCountrySerializer

from dref.models import (
    Dref,
    PlannedIntervention,
    PlannedInterventionIndicators,
    NationalSocietyAction,
    IdentifiedNeed,
    RiskSecurity,
    DrefFile,
    DrefOperationalUpdate,
    DrefFinalReport,
)

from .tasks import send_dref_email
from dref.utils import get_dref_users


class RiskSecuritySerializer(ModelSerializer):
    class Meta:
        model = RiskSecurity
        fields = "__all__"


class PlannedInterventionIndicatorsSerializer(ModelSerializer):
    class Meta:
        model = PlannedInterventionIndicators
        fields = "__all__"


class DrefFileSerializer(ModelSerializer):
    created_by_details = UserNameSerializer(source="created_by", read_only=True)
    file = serializers.FileField(required=False)

    class Meta:
        model = DrefFile
        fields = "__all__"
        read_only_fields = ("created_by",)

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class MiniOperationalUpdateSerializer(serializers.ModelSerializer):
    type_of_onset_display = serializers.CharField(source="get_type_of_onset_display", read_only=True)
    disaster_category_display = serializers.CharField(source="get_disaster_category_display", read_only=True)
    type_of_dref_display = serializers.CharField(source="get_type_of_dref_display", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)

    class Meta:
        model = DrefOperationalUpdate
        fields = [
            "id",
            "title",
            "national_society",
            "disaster_type",
            "type_of_onset",
            "type_of_dref",
            "disaster_category",
            "disaster_category_display",
            "type_of_onset_display",
            "type_of_dref_display",
            "appeal_code",
            "created_at",
            "operational_update_number",
            "country",
            "country_details"
        ]


class MiniDrefFinalReportSerializer(serializers.ModelSerializer):
    type_of_dref_display = serializers.CharField(source="get_type_of_dref_display", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)

    class Meta:
        model = DrefFinalReport
        fields = [
            "id",
            "title",
            "is_published",
            "national_society",
            "disaster_type",
            "type_of_dref_display",
            "appeal_code",
            "created_at",
            "country",
            "country_details"
        ]


class MiniDrefSerializer(serializers.ModelSerializer):
    type_of_onset_display = serializers.CharField(source="get_type_of_onset_display", read_only=True)
    disaster_category_display = serializers.CharField(source="get_disaster_category_display", read_only=True)
    type_of_dref_display = serializers.CharField(source="get_type_of_dref_display", read_only=True)
    operational_update_details = MiniOperationalUpdateSerializer(
        source="drefoperationalupdate_set", many=True, read_only=True
    )
    final_report_details = MiniDrefFinalReportSerializer(source="dreffinalreport", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)

    class Meta:
        model = Dref
        fields = [
            "id",
            "title",
            "national_society",
            "disaster_type",
            "type_of_onset",
            "type_of_dref",
            "disaster_category",
            "disaster_category_display",
            "type_of_onset_display",
            "type_of_dref_display",
            "appeal_code",
            "created_at",
            "operational_update_details",
            "final_report_details",
            "country",
            "country_details"
        ]


class PlannedInterventionSerializer(ModelSerializer):
    budget_file_details = DrefFileSerializer(source="budget_file", read_only=True)
    image_url = serializers.SerializerMethodField()
    indicators = PlannedInterventionIndicatorsSerializer(many=True, required=False)
    title_display = serializers.CharField(source="get_title_display", read_only=True)

    class Meta:
        model = PlannedIntervention
        fields = "__all__"

    def create(self, validated_data):
        indicators = validated_data.pop("indicators", [])
        intervention = super().create(validated_data)
        for indicator in indicators:
            ind_object = PlannedInterventionIndicators.objects.create(**indicator)
            intervention.indicators.add(ind_object)
        return intervention

    def update(self, instance, validated_data):
        # TODO: implement this
        indicators = validated_data.pop("indicators", [])
        intervention = super().update(instance, validated_data)
        return intervention

    def get_image_url(self, plannedintervention):
        title = plannedintervention.title
        if title and self.context and "request" in self.context:
            request = self.context["request"]
            return PlannedIntervention.get_image_map(title, request)
        return None


class NationalSocietyActionSerializer(ModelSerializer):
    image_url = serializers.SerializerMethodField()
    title_display = serializers.CharField(source="get_title_display", read_only=True)

    class Meta:
        model = NationalSocietyAction
        fields = (
            "id",
            "title",
            "description",
            "image_url",
            "title_display",
        )

    def get_image_url(self, nationalsocietyactions):
        title = nationalsocietyactions.title
        if title and self.context and "request" in self.context:
            request = self.context["request"]
            return NationalSocietyAction.get_image_map(title, request)
        return None


class IdentifiedNeedSerializer(ModelSerializer):
    image_url = serializers.SerializerMethodField()
    title_display = serializers.CharField(source="get_title_display", read_only=True)

    class Meta:
        model = IdentifiedNeed
        fields = (
            "id",
            "title",
            "description",
            "image_url",
            "title_display",
        )

    def get_image_url(self, identifiedneed):
        title = identifiedneed.title
        if title and self.context and "request" in self.context:
            request = self.context["request"]
            return IdentifiedNeed.get_image_map(title, request)
        return None


class DrefSerializer(NestedUpdateMixin, NestedCreateMixin, ModelSerializer):
    MAX_NUMBER_OF_IMAGES = 2
    ALLOWED_BUDGET_FILE_EXTENSIONS = ["pdf"]
    ALLOWED_ASSESSMENT_REPORT_EXTENSIONS = ["pdf", "docx", "pptx"]
    MAX_OPERATION_TIMEFRAME = 30
    ASSESSMENT_REPORT_MAX_OPERATION_TIMEFRAME = 2
    national_society_actions = NationalSocietyActionSerializer(many=True, required=False)
    needs_identified = IdentifiedNeedSerializer(many=True, required=False)
    planned_interventions = PlannedInterventionSerializer(many=True, required=False)
    type_of_onset_display = serializers.CharField(source="get_type_of_onset_display", read_only=True)
    type_of_dref_display = serializers.CharField(source="get_type_of_dref_display", read_only=True)
    disaster_category_display = serializers.CharField(source="get_disaster_category_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    modified_by_details = UserNameSerializer(source="modified_by", read_only=True)
    event_map_file = DrefFileSerializer(source="event_map", required=False, allow_null=True)
    images_file = DrefFileSerializer(many=True, required=False, allow_null=True, source="images")
    # field_report_details = MiniFieldReportSerializer(source='field_report', read_only=True)
    created_by_details = UserNameSerializer(source="created_by", read_only=True)
    users_details = UserNameSerializer(source="users", many=True, read_only=True)
    budget_file_details = DrefFileSerializer(source="budget_file", read_only=True)
    cover_image_file = DrefFileSerializer(source="cover_image", required=False, allow_null=True)
    disaster_type_details = DisasterTypeSerializer(source="disaster_type", read_only=True)
    operational_update_details = MiniOperationalUpdateSerializer(
        source="drefoperationalupdate_set", many=True, read_only=True
    )
    dref_final_report_details = MiniDrefFinalReportSerializer(source="dreffinalreport", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)
    district_details = MiniDistrictSerializer(source="district", read_only=True, many=True)
    assessment_report_details = DrefFileSerializer(source="assessment_report", read_only=True)
    supporting_document_details = DrefFileSerializer(read_only=True, source="supporting_document")
    risk_security = RiskSecuritySerializer(many=True, required=False)
    modified_at = serializers.DateTimeField(required=False)
    dref_access_user_list = serializers.SerializerMethodField()

    class Meta:
        model = Dref
        read_only_fields = ("modified_by", "created_by", "budget_file_preview")
        exclude = ("cover_image", "event_map", "images")

    def get_dref_access_user_list(self, obj):
        dref_users_list = get_dref_users()
        for dref in dref_users_list:
            if obj.id == dref["id"]:
                return dref["users"]
        return

    def to_representation(self, instance):
        def _remove_digits_after_decimal(value):
            # NOTE: We are doing this to remove decimal after 3 digits whole numbers
            # eg: 100.00% be replaced with 100%
            if value and len(value.split(".")[0]) == 3:
                return value.split(".")[0]
            return value

        data = super().to_representation(instance)
        for key in [
            "disability_people_per",
            "people_per_urban",
            "people_per_local",
        ]:
            value = data.get(key) or ""
            data[key] = _remove_digits_after_decimal(value)
        return data

    def validate(self, data):
        event_date = data.get("event_date")
        operation_timeframe = data.get("operation_timeframe")
        is_assessment_report = data.get("is_assessment_report")
        if event_date and data["type_of_onset"] not in [Dref.OnsetType.SLOW, Dref.OnsetType.SUDDEN]:
            raise serializers.ValidationError(
                {
                    "event_date": gettext(
                        "Cannot add event_date if onset type not in %s or %s"
                        % (Dref.OnsetType.SLOW.label, Dref.OnsetType.SUDDEN.label)
                    )
                }
            )
        if self.instance and self.instance.is_published:
            raise serializers.ValidationError("Published Dref can't be changed. Please contact Admin")
        if self.instance and DrefFinalReport.objects.filter(dref=self.instance, is_published=True).exists():
            raise serializers.ValidationError(gettext("Can't Update %s dref for publish Field Report" % self.instance.id))
        if operation_timeframe and is_assessment_report and operation_timeframe > 30:
            raise serializers.ValidationError(
                gettext("Operation timeframe can't be greater than %s for assessment_report" % self.MAX_OPERATION_TIMEFRAME)
            )
        return data

    def validate_images(self, images):
        # Don't allow images more than MAX_NUMBER_OF_IMAGES
        if len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(gettext("Can add utmost %s images" % self.MAX_NUMBER_OF_IMAGES))
        images_id = [image.id for image in images]
        images_without_access_qs = DrefFile.objects.filter(
            # Not created by current user
            ~models.Q(created_by=self.context["request"].user),
            # Look into provided images
            id__in=images_id,
        )
        # Exclude already attached images if exists
        if self.instance:
            images_without_access_qs = images_without_access_qs.exclude(id__in=self.instance.images.all())
        images_id_without_access = images_without_access_qs.values_list("id", flat=True)
        if images_id_without_access:
            raise serializers.ValidationError(
                gettext(
                    "Only image owner can attach image. Not allowed image ids: %s"
                    % ",".join(map(str, images_id_without_access))
                )
            )
        return images

    def validate_budget_file(self, budget_file):
        if budget_file is None:
            return
        extension = os.path.splitext(budget_file.file.name)[1].replace(".", "")
        if extension.lower() not in self.ALLOWED_BUDGET_FILE_EXTENSIONS:
            raise serializers.ValidationError(f"Invalid uploaded file extension: {extension}, Supported only PDF Files")
        return budget_file

    def validate_assessment_report(self, assessment_report):
        if assessment_report is None:
            return
        extension = os.path.splitext(assessment_report.file.name)[1].replace(".", "")
        if extension.lower() not in self.ALLOWED_ASSESSMENT_REPORT_EXTENSIONS:
            raise serializers.ValidationError(
                f"Invalid uploaded file extension: {extension}, Supported only {self.ALLOWED_ASSESSMENT_REPORT_EXTENSIONS} Files"
            )
        return assessment_report

    def validate_operation_timeframe(self, operation_timeframe):
        if operation_timeframe and operation_timeframe > self.MAX_OPERATION_TIMEFRAME:
            raise serializers.ValidationError(
                gettext(f"Operation timeframe can't be greater than {self.MAX_OPERATION_TIMEFRAME}")
            )
        return operation_timeframe

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        type_of_dref = validated_data.get("type_of_dref")
        if type_of_dref and type_of_dref == Dref.DrefType.ASSESSMENT:
            # Previous Operations
            validated_data["lessons_learned"] = None
            validated_data["did_it_affect_same_area"] = None
            validated_data["did_it_affect_same_population"] = None
            validated_data["did_ns_respond"] = None
            validated_data["did_ns_request_fund"] = None
            validated_data["assessment_report"] = None
            # Event Description
            validated_data["event_scope"] = None
            validated_data["identified_gaps"] = None
            # Targeted Population
            validated_data["women"] = None
            validated_data["men"] = None
            validated_data["girls"] = None
            validated_data["boys"] = None
            # Support Services
            validated_data["logistic_capacity_of_ns"] = None
            validated_data["pmer"] = None
            validated_data["communication"] = None
            dref_assessment_report = super().create(validated_data)
            dref_assessment_report.needs_identified.clear()
            return dref_assessment_report
        if "users" in validated_data:
            to = {u.email for u in validated_data["users"]}
        else:
            to = None
        dref = super().create(validated_data)
        if to:
            transaction.on_commit(lambda: send_dref_email.delay(dref.id, list(to), "New"))
        return dref

    def update(self, instance, validated_data):
        validated_data["modified_by"] = self.context["request"].user
        modified_at = validated_data.pop("modified_at", None)
        type_of_dref = validated_data.get("type_of_dref")
        if modified_at is None:
            raise serializers.ValidationError({"modified_at": "Modified At is required!"})
        if type_of_dref and type_of_dref == Dref.DrefType.ASSESSMENT:
            # Previous Operations
            validated_data["lessons_learned"] = None
            validated_data["did_it_affect_same_area"] = None
            validated_data["did_it_affect_same_population"] = None
            validated_data["did_ns_respond"] = None
            validated_data["did_ns_request_fund"] = None
            validated_data["ns_request_text"] = None
            validated_data["dref_recurrent_text"] = None
            validated_data["assessment_report"] = None
            # Event Description
            validated_data["event_scope"] = None
            validated_data["identified_gaps"] = None
            # Targeted Population
            validated_data["women"] = None
            validated_data["men"] = None
            validated_data["girls"] = None
            validated_data["boys"] = None
            # Support Services
            validated_data["logistic_capacity_of_ns"] = None
            validated_data["pmer"] = None
            validated_data["communication"] = None
            dref_assessment_report = super().update(instance, validated_data)
            dref_assessment_report.needs_identified.clear()
            return dref_assessment_report

        # we don't send notification again to the already notified users:
        if "users" in validated_data:
            to = {u.email for u in validated_data["users"] if u.email not in {t.email for t in instance.users.iterator()}}
        else:
            to = None
        if modified_at and instance.modified_at and modified_at < instance.modified_at:
            raise serializers.ValidationError({"modified_at": settings.DREF_OP_UPDATE_FINAL_REPORT_UPDATE_ERROR_MESSAGE})
        dref = super().update(instance, validated_data)
        if to:
            transaction.on_commit(lambda: send_dref_email.delay(dref.id, list(to), "Updated"))
        return dref


class DrefOperationalUpdateSerializer(NestedUpdateMixin, NestedCreateMixin, serializers.ModelSerializer):
    national_society_actions = NationalSocietyActionSerializer(many=True, required=False)
    needs_identified = IdentifiedNeedSerializer(many=True, required=False)
    planned_interventions = PlannedInterventionSerializer(many=True, required=False)
    type_of_onset_display = serializers.CharField(source="get_type_of_onset_display", read_only=True)
    type_of_dref_display = serializers.CharField(source="get_type_of_dref_display", read_only=True)
    disaster_category_display = serializers.CharField(source="get_disaster_category_display", read_only=True)
    created_by_details = UserNameSerializer(source="created_by", read_only=True)
    event_map_file = DrefFileSerializer(source="event_map", required=False, allow_null=True)
    cover_image_file = DrefFileSerializer(source="cover_image", required=False, allow_null=True)
    images_file = DrefFileSerializer(many=True, required=False, allow_null=True, source="images")
    photos_file = DrefFileSerializer(source="photos", many=True, required=False, allow_null=True)
    modified_by_details = UserNameSerializer(source="modified_by", read_only=True)
    disaster_type_details = DisasterTypeSerializer(source="disaster_type", read_only=True)
    budget_file_details = DrefFileSerializer(source="budget_file", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)
    district_details = MiniDistrictSerializer(source="district", read_only=True, many=True)
    assessment_report_details = DrefFileSerializer(source="assessment_report", read_only=True)
    risk_security = RiskSecuritySerializer(many=True, required=False)
    modified_at = serializers.DateTimeField(required=False)
    created_by_details = UserNameSerializer(source="created_by", read_only=True)
    users_details = UserNameSerializer(source="users", many=True, read_only=True)

    class Meta:
        model = DrefOperationalUpdate
        read_only_fields = ("operational_update_number",)
        exclude = ("images", "photos", "event_map", "cover_image")

    def validate(self, data):
        dref = data.get("dref")
        if not self.instance and dref:
            if not dref.is_published:
                raise serializers.ValidationError(
                    gettext("Can't create Operational Update for not published %s dref." % dref.id)
                )
            # get the latest dref_operation_update and check whether it is published or not, exclude no operational object created so far
            dref_operational_update = (
                DrefOperationalUpdate.objects.filter(dref=dref).order_by("-operational_update_number").first()
            )
            if dref_operational_update and not dref_operational_update.is_published:
                raise serializers.ValidationError(
                    gettext(
                        "Can't create Operational Update for not published Operational Update %s id and Operational Update Number %i."
                        % (dref_operational_update.id, dref_operational_update.operational_update_number)
                    )
                )

        return data

    def validate_appeal_code(self, appeal_code):
        if appeal_code != self.instance.appeal_code:
            raise serializers.ValidationError("Can't edit MDR Code")
        return appeal_code

    def get_total_timeframe(self, start_date, end_date):
        if start_date and end_date:
            start_date_month = datetime.datetime.strftime("%m")
            end_date_month = datetime.datetime.strptime("%m")
            return abs(end_date_month - start_date_month)
        return None

    def create(self, validated_data):
        dref = validated_data["dref"]
        dref_operational_update = (
            DrefOperationalUpdate.objects.filter(dref=dref).order_by("-operational_update_number").first()
        )
        if not dref_operational_update:
            validated_data["title"] = dref.title
            validated_data["title_prefix"] = dref.title_prefix
            validated_data["national_society"] = dref.national_society
            validated_data["disaster_type"] = dref.disaster_type
            validated_data["type_of_onset"] = dref.type_of_onset
            validated_data["type_of_dref"] = dref.type_of_dref
            validated_data["disaster_category"] = dref.disaster_category
            validated_data["number_of_people_targeted"] = dref.num_assisted
            validated_data["number_of_people_affected"] = dref.num_affected
            validated_data["emergency_appeal_planned"] = dref.emergency_appeal_planned
            validated_data["appeal_code"] = dref.appeal_code
            validated_data["glide_code"] = dref.glide_code
            validated_data["ifrc_appeal_manager_name"] = dref.ifrc_appeal_manager_name
            validated_data["ifrc_appeal_manager_email"] = dref.ifrc_appeal_manager_email
            validated_data["ifrc_appeal_manager_title"] = dref.ifrc_appeal_manager_title
            validated_data["ifrc_appeal_manager_phone_number"] = dref.ifrc_appeal_manager_phone_number
            validated_data["ifrc_project_manager_name"] = dref.ifrc_project_manager_name
            validated_data["ifrc_project_manager_email"] = dref.ifrc_project_manager_email
            validated_data["ifrc_project_manager_title"] = dref.ifrc_project_manager_title
            validated_data["ifrc_project_manager_phone_number"] = dref.ifrc_project_manager_phone_number
            validated_data["national_society_contact_name"] = dref.national_society_contact_name
            validated_data["national_society_contact_email"] = dref.national_society_contact_email
            validated_data["national_society_contact_title"] = dref.national_society_contact_title
            validated_data["national_society_contact_phone_number"] = dref.national_society_contact_phone_number
            validated_data["media_contact_name"] = dref.media_contact_name
            validated_data["media_contact_email"] = dref.media_contact_email
            validated_data["media_contact_title"] = dref.media_contact_title
            validated_data["media_contact_phone_number"] = dref.media_contact_phone_number
            validated_data["ifrc_emergency_name"] = dref.ifrc_emergency_name
            validated_data["ifrc_emergency_title"] = dref.ifrc_emergency_title
            validated_data["ifrc_emergency_phone_number"] = dref.ifrc_emergency_phone_number
            validated_data["ifrc_emergency_email"] = dref.ifrc_emergency_email
            validated_data["regional_focal_point_email"] = dref.regional_focal_point_email
            validated_data["regional_focal_point_name"] = dref.regional_focal_point_name
            validated_data["regional_focal_point_title"] = dref.regional_focal_point_title
            validated_data["regional_focal_point_phone_number"] = dref.regional_focal_point_phone_number
            validated_data["ifrc"] = dref.ifrc
            validated_data["icrc"] = dref.icrc
            validated_data["partner_national_society"] = dref.partner_national_society
            validated_data["government_requested_assistance"] = dref.government_requested_assistance
            validated_data["national_authorities"] = dref.national_authorities
            validated_data["un_or_other_actor"] = dref.un_or_other_actor
            validated_data["major_coordination_mechanism"] = dref.major_coordination_mechanism
            validated_data["people_assisted"] = dref.people_assisted
            validated_data["selection_criteria"] = dref.selection_criteria
            validated_data["entity_affected"] = dref.entity_affected
            validated_data["women"] = dref.women
            validated_data["men"] = dref.men
            validated_data["girls"] = dref.girls
            validated_data["boys"] = dref.boys
            validated_data["disability_people_per"] = dref.disability_people_per
            validated_data["people_per_urban"] = dref.people_per_urban
            validated_data["people_per_local"] = dref.people_per_local
            validated_data["people_targeted_with_early_actions"] = dref.people_targeted_with_early_actions
            validated_data["displaced_people"] = dref.displaced_people
            validated_data["operation_objective"] = dref.operation_objective
            validated_data["response_strategy"] = dref.response_strategy
            validated_data["created_by"] = self.context["request"].user
            validated_data["new_operational_start_date"] = dref.date_of_approval
            validated_data["operational_update_number"] = 1  # if no any dref operational update created so far
            validated_data["dref_allocated_so_far"] = dref.amount_requested
            validated_data["event_description"] = dref.event_description
            validated_data["anticipatory_actions"] = dref.anticipatory_actions
            validated_data["event_scope"] = dref.event_scope
            validated_data["budget_file"] = dref.budget_file
            validated_data["country"] = dref.country
            validated_data["risk_security_concern"] = dref.risk_security_concern
            validated_data["event_date"] = dref.event_date
            validated_data["ns_respond_date"] = dref.ns_respond_date
            validated_data["did_ns_respond"] = dref.did_ns_respond
            validated_data["total_targeted_population"] = dref.total_targeted_population
            validated_data["is_there_major_coordination_mechanism"] = dref.is_there_major_coordination_mechanism
            validated_data["human_resource"] = dref.human_resource
            validated_data["is_surge_personnel_deployed"] = dref.is_surge_personnel_deployed
            validated_data["surge_personnel_deployed"] = dref.surge_personnel_deployed
            validated_data["logistic_capacity_of_ns"] = dref.logistic_capacity_of_ns
            validated_data["safety_concerns"] = dref.safety_concerns
            validated_data["pmer"] = dref.pmer
            validated_data["people_in_need"] = dref.people_in_need
            validated_data["communication"] = dref.communication
            validated_data["total_operation_timeframe"] = dref.operation_timeframe
            validated_data["ns_request_date"] = dref.ns_request_date
            validated_data["date_of_approval"] = dref.date_of_approval
            operational_update = super().create(validated_data)
            # XXX: Copy files from DREF (Only nested serialized fields)
            nested_serialized_file_fields = [
                "cover_image",
                "event_map",
            ]
            for file_field in nested_serialized_file_fields:
                dref_file = getattr(dref, file_field, None)
                if dref_file:
                    setattr(operational_update, file_field, dref_file.clone(self.context["request"].user))
            operational_update.save(update_fields=nested_serialized_file_fields)
            # M2M Fields
            operational_update.planned_interventions.add(*dref.planned_interventions.all())
            operational_update.images.add(*dref.images.all())
            operational_update.national_society_actions.add(*dref.national_society_actions.all())
            operational_update.needs_identified.add(*dref.needs_identified.all())
            operational_update.district.add(*dref.district.all())
            operational_update.users.add(*dref.users.all())
            operational_update.risk_security.add(*dref.risk_security.all())
        else:
            # get the latest dref operational update
            validated_data["title"] = dref_operational_update.title
            validated_data["title_prefix"] = dref_operational_update.title_prefix
            validated_data["national_society"] = dref_operational_update.national_society
            validated_data["disaster_type"] = dref_operational_update.disaster_type
            validated_data["type_of_onset"] = dref_operational_update.type_of_onset
            validated_data["type_of_dref"] = dref.type_of_dref
            validated_data["disaster_category"] = dref_operational_update.disaster_category
            validated_data["number_of_people_targeted"] = dref_operational_update.number_of_people_targeted
            validated_data["number_of_people_affected"] = dref_operational_update.number_of_people_affected
            validated_data["emergency_appeal_planned"] = dref_operational_update.emergency_appeal_planned
            validated_data["appeal_code"] = dref_operational_update.appeal_code
            validated_data["glide_code"] = dref_operational_update.glide_code
            validated_data["ifrc_appeal_manager_name"] = dref_operational_update.ifrc_appeal_manager_name
            validated_data["ifrc_appeal_manager_email"] = dref_operational_update.ifrc_appeal_manager_email
            validated_data["ifrc_appeal_manager_title"] = dref_operational_update.ifrc_appeal_manager_title
            validated_data["ifrc_appeal_manager_phone_number"] = dref_operational_update.ifrc_appeal_manager_phone_number
            validated_data["ifrc_project_manager_name"] = dref_operational_update.ifrc_project_manager_name
            validated_data["ifrc_project_manager_email"] = dref_operational_update.ifrc_project_manager_email
            validated_data["ifrc_project_manager_title"] = dref_operational_update.ifrc_project_manager_title
            validated_data["ifrc_project_manager_phone_number"] = dref_operational_update.ifrc_project_manager_phone_number
            validated_data["national_society_contact_name"] = dref_operational_update.national_society_contact_name
            validated_data["national_society_contact_email"] = dref_operational_update.national_society_contact_email
            validated_data["national_society_contact_title"] = dref_operational_update.national_society_contact_title
            validated_data[
                "national_society_contact_phone_number"
            ] = dref_operational_update.national_society_contact_phone_number
            validated_data["media_contact_name"] = dref_operational_update.media_contact_name
            validated_data["media_contact_email"] = dref_operational_update.media_contact_email
            validated_data["media_contact_title"] = dref_operational_update.media_contact_title
            validated_data["media_contact_phone_number"] = dref_operational_update.media_contact_phone_number
            validated_data["ifrc_emergency_name"] = dref_operational_update.ifrc_emergency_name
            validated_data["ifrc_emergency_title"] = dref_operational_update.ifrc_emergency_title
            validated_data["ifrc_emergency_phone_number"] = dref_operational_update.ifrc_emergency_phone_number
            validated_data["ifrc_emergency_email"] = dref_operational_update.ifrc_emergency_email
            validated_data["regional_focal_point_email"] = dref_operational_update.regional_focal_point_email
            validated_data["regional_focal_point_name"] = dref_operational_update.regional_focal_point_name
            validated_data["regional_focal_point_title"] = dref_operational_update.regional_focal_point_title
            validated_data["regional_focal_point_phone_number"] = dref_operational_update.regional_focal_point_phone_number
            validated_data["ifrc"] = dref_operational_update.ifrc
            validated_data["icrc"] = dref_operational_update.icrc
            validated_data["partner_national_society"] = dref_operational_update.partner_national_society
            validated_data["government_requested_assistance"] = dref_operational_update.government_requested_assistance
            validated_data["national_authorities"] = dref_operational_update.national_authorities
            validated_data["un_or_other_actor"] = dref_operational_update.un_or_other_actor
            validated_data["major_coordination_mechanism"] = dref_operational_update.major_coordination_mechanism
            validated_data["people_assisted"] = dref_operational_update.people_assisted
            validated_data["selection_criteria"] = dref_operational_update.selection_criteria
            validated_data["entity_affected"] = dref_operational_update.entity_affected
            validated_data["women"] = dref_operational_update.women
            validated_data["men"] = dref_operational_update.men
            validated_data["girls"] = dref_operational_update.girls
            validated_data["boys"] = dref_operational_update.boys
            validated_data["disability_people_per"] = dref_operational_update.disability_people_per
            validated_data["people_per_urban"] = dref_operational_update.people_per_urban
            validated_data["people_per_local"] = dref_operational_update.people_per_local
            validated_data["people_targeted_with_early_actions"] = dref_operational_update.people_targeted_with_early_actions
            validated_data["displaced_people"] = dref_operational_update.displaced_people
            validated_data["operation_objective"] = dref_operational_update.operation_objective
            validated_data["response_strategy"] = dref_operational_update.response_strategy
            validated_data["created_by"] = self.context["request"].user
            validated_data["operational_update_number"] = dref_operational_update.operational_update_number + 1
            validated_data["new_operational_start_date"] = dref_operational_update.dref.date_of_approval
            validated_data["dref_allocated_so_far"] = dref_operational_update.total_dref_allocation
            validated_data["event_description"] = dref_operational_update.event_description
            validated_data["anticipatory_actions"] = dref_operational_update.anticipatory_actions
            validated_data["event_scope"] = dref_operational_update.event_scope
            validated_data["budget_file"] = dref_operational_update.budget_file
            validated_data["assessment_report"] = dref_operational_update.assessment_report
            validated_data["country"] = dref_operational_update.country
            validated_data["risk_security_concern"] = dref_operational_update.risk_security_concern
            validated_data["event_date"] = dref_operational_update.event_date
            validated_data["ns_respond_date"] = dref_operational_update.ns_respond_date
            validated_data["did_ns_respond"] = dref_operational_update.did_ns_respond
            validated_data["total_targeted_population"] = dref_operational_update.total_targeted_population
            validated_data[
                "is_there_major_coordination_mechanism"
            ] = dref_operational_update.is_there_major_coordination_mechanism
            validated_data["human_resource"] = dref_operational_update.human_resource
            validated_data["is_surge_personnel_deployed"] = dref_operational_update.is_surge_personnel_deployed
            validated_data["surge_personnel_deployed"] = dref_operational_update.surge_personnel_deployed
            validated_data["logistic_capacity_of_ns"] = dref_operational_update.logistic_capacity_of_ns
            validated_data["safety_concerns"] = dref_operational_update.safety_concerns
            validated_data["pmer"] = dref_operational_update.pmer
            validated_data["communication"] = dref_operational_update.communication
            validated_data["people_in_need"] = dref_operational_update.people_in_need
            validated_data["total_operation_timeframe"] = dref_operational_update.total_operation_timeframe
            validated_data["ns_request_date"] = dref_operational_update.ns_request_date
            validated_data["date_of_approval"] = dref_operational_update.date_of_approval
            operational_update = super().create(validated_data)
            # XXX: Copy files from DREF (Only nested serialized fields)
            nested_serialized_file_fields = [
                "cover_image",
                "event_map",
            ]
            for file_field in nested_serialized_file_fields:
                dref_file = getattr(dref, file_field, None)
                if dref_file:
                    setattr(operational_update, file_field, dref_file.clone(self.context["request"].user))
            operational_update.save(update_fields=nested_serialized_file_fields)
            # XXX COPY M2M fields
            operational_update.planned_interventions.add(*dref_operational_update.planned_interventions.all())
            operational_update.images.add(*dref_operational_update.images.all())
            operational_update.national_society_actions.add(*dref_operational_update.national_society_actions.all())
            operational_update.needs_identified.add(*dref_operational_update.needs_identified.all())
            operational_update.district.add(*dref_operational_update.district.all())
            operational_update.users.add(*dref_operational_update.users.all())
            operational_update.risk_security.add(*dref_operational_update.risk_security.all())
        return operational_update

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        # changing_timeframe_operation = validated_data.get(
        #     "changing_timeframe_operation", instance.changing_timeframe_operation
        # )
        # total_operation_timeframe = validated_data.get("total_operation_timeframe", instance.total_operation_timeframe)
        number_of_people_targeted = validated_data.get("number_of_people_targeted", instance.number_of_people_targeted)
        request_for_second_allocation = validated_data.get(
            "request_for_second_allocation", instance.request_for_second_allocation
        )
        additional_allocation = validated_data.get("additional_allocation", instance.additional_allocation)
        changing_target_population_of_operation = validated_data.get(
            "changing_target_population_of_operation", instance.changing_target_population_of_operation
        )
        changing_geographic_location = validated_data.get(
            "changing_geographic_location", instance.changing_geographic_location
        )
        district = validated_data.get("district", instance.district)
        dref_operation_timeframe = validated_data.get("dref", instance.dref).operation_timeframe
        dref_target_population_of_operation = validated_data.get("dref", instance.dref).total_targeted_population
        dref_amount_requested = validated_data.get("dref", instance.dref).amount_requested
        dref_district = validated_data.get("dref", instance.dref).district.all()
        modified_at = validated_data.pop("modified_at", None)
        if modified_at is None:
            raise serializers.ValidationError({"modified_at": "Modified At is required!"})

        # if (
        #     (not changing_timeframe_operation)
        #     and total_operation_timeframe
        #     and dref_operation_timeframe
        #     and total_operation_timeframe != dref_operation_timeframe
        # ):
        #     raise serializers.ValidationError(
        #         "Found diffrent operation timeframe for dref and operational update with changing not set to true"
        #     )

        # if (
        #     changing_timeframe_operation
        #     and total_operation_timeframe
        #     and dref_operation_timeframe
        #     and total_operation_timeframe == dref_operation_timeframe
        # ):
        #     raise serializers.ValidationError(
        #         "Found same operation timeframe for dref and operational update with changing set to true"
        #     )

        if (
            (not changing_target_population_of_operation)
            and number_of_people_targeted
            and dref_target_population_of_operation
            and dref_target_population_of_operation != number_of_people_targeted
        ):
            raise serializers.ValidationError(
                "Found diffrent targeted population for dref and operational update with changing not set to true"
            )

        if (
            changing_target_population_of_operation
            and number_of_people_targeted
            and dref_target_population_of_operation
            and dref_target_population_of_operation == number_of_people_targeted
        ):
            raise serializers.ValidationError(
                "Found same targeted population for dref and operational update with changing set to true"
            )

        # if request_for_second_allocation and additional_allocation and dref_amount_requested != additional_allocation:
        #     raise serializers.ValidationError('Found diffrent allocation for dref and operation update')

        if (not changing_geographic_location) and district and dref_district and set(district) != set(dref_district):
            raise serializers.ValidationError(
                "Found different district for dref and operational update with changing not set to true"
            )

        if changing_geographic_location and district and dref_district and set(district) == set(dref_district):
            raise serializers.ValidationError(
                "Found same district for dref and operational update with changing set to true"
            )

        if modified_at and instance.modified_at and modified_at < instance.modified_at:
            raise serializers.ValidationError({"modified_at": settings.DREF_OP_UPDATE_FINAL_REPORT_UPDATE_ERROR_MESSAGE})
        return super().update(instance, validated_data)


class DrefFinalReportSerializer(NestedUpdateMixin, NestedCreateMixin, serializers.ModelSerializer):
    MAX_NUMBER_OF_PHOTOS = 2
    national_society_actions = NationalSocietyActionSerializer(many=True, required=False)
    needs_identified = IdentifiedNeedSerializer(many=True, required=False)
    planned_interventions = PlannedInterventionSerializer(many=True, required=False)
    type_of_onset_display = serializers.CharField(source="get_type_of_onset_display", read_only=True)
    type_of_dref_display = serializers.CharField(source="get_type_of_dref_display", read_only=True)
    disaster_category_display = serializers.CharField(source="get_disaster_category_display", read_only=True)
    created_by_details = UserNameSerializer(source="created_by", read_only=True)
    event_map_file = DrefFileSerializer(source="event_map", required=False, allow_null=True)
    cover_image_file = DrefFileSerializer(source="cover_image", required=False, allow_null=True)
    images_file = DrefFileSerializer(many=True, required=False, allow_null=True, source="images")
    photos_file = DrefFileSerializer(source="photos", many=True, required=False, allow_null=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)
    district_details = MiniDistrictSerializer(source="district", read_only=True, many=True)
    assessment_report_details = DrefFileSerializer(source="assessment_report", read_only=True)
    risk_security = RiskSecuritySerializer(many=True, required=False)
    modified_at = serializers.DateTimeField(required=False)
    financial_report_details = DrefFileSerializer(source="financial_report", read_only=True)
    created_by_details = UserNameSerializer(source="created_by", read_only=True)
    users_details = UserNameSerializer(source="users", many=True, read_only=True)

    class Meta:
        model = DrefFinalReport
        exclude = (
            "images",
            "photos",
            "event_map",
            "cover_image",
        )

    def validate(self, data):
        dref = data.get("dref")
        # check if dref is published and operational_update associated with it is also published
        if not self.instance and dref:
            if not dref.is_published:
                raise serializers.ValidationError(gettext("Can't create Final Report for not published dref %s." % dref.id))
            dref_operational_update = DrefOperationalUpdate.objects.filter(
                dref=dref,
                is_published=False,
            ).values_list("id", flat=True)
            if dref_operational_update:
                raise serializers.ValidationError(
                    gettext(
                        "Can't create Final Report for not published Operational Update %s ids "
                        % ",".join(map(str, dref_operational_update))
                    )
                )
        if self.instance and self.instance.is_published:
            raise serializers.ValidationError(gettext("Can't update published final report %s." % self.instance.id))
        return data

    def validate_photos(self, photos):
        if photos and len(photos) > self.MAX_NUMBER_OF_PHOTOS:
            raise serializers.ValidationError("Can add utmost %s photos" % self.MAX_NUMBER_OF_PHOTOS)
        return photos

    def create(self, validated_data):
        # here check if there is operational update for corresponding dref
        # if yes copy from the latest operational update
        # else copy from dref
        dref = validated_data["dref"]
        dref_operational_update = (
            DrefOperationalUpdate.objects.filter(dref=dref, is_published=True).order_by("-operational_update_number").first()
        )
        if dref_operational_update:
            validated_data["title"] = dref_operational_update.title
            validated_data["title_prefix"] = dref_operational_update.title_prefix
            validated_data["national_society"] = dref_operational_update.national_society
            validated_data["disaster_type"] = dref_operational_update.disaster_type
            validated_data["type_of_onset"] = dref_operational_update.type_of_onset
            validated_data["type_of_dref"] = dref_operational_update.type_of_dref
            validated_data["disaster_category"] = dref_operational_update.disaster_category
            validated_data["number_of_people_targeted"] = dref_operational_update.number_of_people_targeted
            validated_data["number_of_people_affected"] = dref_operational_update.number_of_people_affected
            validated_data["total_dref_allocation"] = dref_operational_update.total_dref_allocation
            validated_data["total_operation_timeframe"] = dref_operational_update.total_operation_timeframe
            validated_data["operation_start_date"] = dref_operational_update.dref.date_of_approval
            validated_data["appeal_code"] = dref_operational_update.appeal_code
            validated_data["glide_code"] = dref_operational_update.glide_code
            validated_data["ifrc_appeal_manager_name"] = dref_operational_update.ifrc_appeal_manager_name
            validated_data["ifrc_appeal_manager_email"] = dref_operational_update.ifrc_appeal_manager_email
            validated_data["ifrc_appeal_manager_title"] = dref_operational_update.ifrc_appeal_manager_title
            validated_data["ifrc_appeal_manager_phone_number"] = dref_operational_update.ifrc_appeal_manager_phone_number
            validated_data["ifrc_project_manager_name"] = dref_operational_update.ifrc_project_manager_name
            validated_data["ifrc_project_manager_email"] = dref_operational_update.ifrc_project_manager_email
            validated_data["ifrc_project_manager_title"] = dref_operational_update.ifrc_project_manager_title
            validated_data["ifrc_project_manager_phone_number"] = dref_operational_update.ifrc_project_manager_phone_number
            validated_data["national_society_contact_name"] = dref_operational_update.national_society_contact_name
            validated_data["national_society_contact_email"] = dref_operational_update.national_society_contact_email
            validated_data["national_society_contact_title"] = dref_operational_update.national_society_contact_title
            validated_data[
                "national_society_contact_phone_number"
            ] = dref_operational_update.national_society_contact_phone_number
            validated_data["media_contact_name"] = dref_operational_update.media_contact_name
            validated_data["media_contact_email"] = dref_operational_update.media_contact_email
            validated_data["media_contact_title"] = dref_operational_update.media_contact_title
            validated_data["media_contact_phone_number"] = dref_operational_update.media_contact_phone_number
            validated_data["ifrc_emergency_name"] = dref_operational_update.ifrc_emergency_name
            validated_data["ifrc_emergency_title"] = dref_operational_update.ifrc_emergency_title
            validated_data["ifrc_emergency_phone_number"] = dref_operational_update.ifrc_emergency_phone_number
            validated_data["ifrc_emergency_email"] = dref_operational_update.ifrc_emergency_email
            validated_data["ifrc"] = dref_operational_update.ifrc
            validated_data["icrc"] = dref_operational_update.icrc
            validated_data["partner_national_society"] = dref_operational_update.partner_national_society
            validated_data["government_requested_assistance"] = dref_operational_update.government_requested_assistance
            validated_data["national_authorities"] = dref_operational_update.national_authorities
            validated_data["un_or_other_actor"] = dref_operational_update.un_or_other_actor
            validated_data["major_coordination_mechanism"] = dref_operational_update.major_coordination_mechanism
            validated_data["people_assisted"] = dref_operational_update.people_assisted
            validated_data["selection_criteria"] = dref_operational_update.selection_criteria
            validated_data["entity_affected"] = dref_operational_update.entity_affected
            validated_data["women"] = dref_operational_update.women
            validated_data["men"] = dref_operational_update.men
            validated_data["girls"] = dref_operational_update.girls
            validated_data["boys"] = dref_operational_update.boys
            validated_data["disability_people_per"] = dref_operational_update.disability_people_per
            validated_data["people_per_urban"] = dref_operational_update.people_per_urban
            validated_data["people_per_local"] = dref_operational_update.people_per_local
            validated_data["people_targeted_with_early_actions"] = dref_operational_update.people_targeted_with_early_actions
            validated_data["displaced_people"] = dref_operational_update.displaced_people
            validated_data["operation_objective"] = dref_operational_update.operation_objective
            validated_data["response_strategy"] = dref_operational_update.response_strategy
            validated_data["created_by"] = self.context["request"].user
            validated_data["operation_start_date"] = dref_operational_update.dref.date_of_approval
            validated_data["event_description"] = dref_operational_update.event_description
            validated_data["anticipatory_actions"] = dref_operational_update.anticipatory_actions
            validated_data["event_scope"] = dref_operational_update.event_scope
            validated_data["country"] = dref_operational_update.country
            validated_data["risk_security_concern"] = dref_operational_update.risk_security_concern
            validated_data["total_targeted_population"] = dref_operational_update.total_targeted_population
            validated_data[
                "is_there_major_coordination_mechanism"
            ] = dref_operational_update.is_there_major_coordination_mechanism
            validated_data["event_date"] = dref_operational_update.event_date
            validated_data["people_in_need"] = dref_operational_update.people_in_need
            validated_data["ns_respond_date"] = dref_operational_update.ns_respond_date
            validated_data["assessment_report"] = dref_operational_update.assessment_report

            if validated_data["type_of_dref"] == Dref.DrefType.LOAN:
                raise serializers.ValidationError(gettext("Can't create final report for dref type %s" % Dref.DrefType.LOAN))
            dref_final_report = super().create(validated_data)
            # XXX: Copy files from DREF (Only nested serialized fields)
            nested_serialized_file_fields = [
                "cover_image",
                "event_map",
            ]
            for file_field in nested_serialized_file_fields:
                dref_file = getattr(dref, file_field, None)
                if dref_file:
                    setattr(dref_final_report, file_field, dref_file.clone(self.context["request"].user))
            dref_final_report.save(update_fields=nested_serialized_file_fields)
            dref_final_report.planned_interventions.add(*dref_operational_update.planned_interventions.all())
            dref_final_report.needs_identified.add(*dref_operational_update.needs_identified.all())
            dref_final_report.national_society_actions.add(*dref_operational_update.national_society_actions.all())
            dref_final_report.district.add(*dref_operational_update.district.all())
            dref_final_report.images.add(*dref_operational_update.images.all())
            dref_final_report.photos.add(*dref_operational_update.photos.all())
            dref_final_report.risk_security.add(*dref_operational_update.risk_security.all())
            dref_final_report.users.add(*dref_operational_update.users.all())
        else:
            validated_data["title"] = dref.title
            validated_data["title_prefix"] = dref.title_prefix
            validated_data["national_society"] = dref.national_society
            validated_data["disaster_type"] = dref.disaster_type
            validated_data["type_of_onset"] = dref.type_of_onset
            validated_data["type_of_dref"] = dref.type_of_dref
            validated_data["disaster_category"] = dref.disaster_category
            validated_data["number_of_people_targeted"] = dref.num_assisted
            validated_data["number_of_people_affected"] = dref.num_affected
            validated_data["total_operation_timeframe"] = dref.operation_timeframe
            validated_data["operation_start_date"] = dref.date_of_approval
            validated_data["appeal_code"] = dref.appeal_code
            validated_data["glide_code"] = dref.glide_code
            validated_data["ifrc_appeal_manager_name"] = dref.ifrc_appeal_manager_name
            validated_data["ifrc_appeal_manager_email"] = dref.ifrc_appeal_manager_email
            validated_data["ifrc_appeal_manager_title"] = dref.ifrc_appeal_manager_title
            validated_data["ifrc_appeal_manager_phone_number"] = dref.ifrc_appeal_manager_phone_number
            validated_data["ifrc_project_manager_name"] = dref.ifrc_project_manager_name
            validated_data["ifrc_project_manager_email"] = dref.ifrc_project_manager_email
            validated_data["ifrc_project_manager_title"] = dref.ifrc_project_manager_title
            validated_data["ifrc_project_manager_phone_number"] = dref.ifrc_project_manager_phone_number
            validated_data["national_society_contact_name"] = dref.national_society_contact_name
            validated_data["national_society_contact_email"] = dref.national_society_contact_email
            validated_data["national_society_contact_title"] = dref.national_society_contact_title
            validated_data["national_society_contact_phone_number"] = dref.national_society_contact_phone_number
            validated_data["media_contact_name"] = dref.media_contact_name
            validated_data["media_contact_email"] = dref.media_contact_email
            validated_data["media_contact_title"] = dref.media_contact_title
            validated_data["media_contact_phone_number"] = dref.media_contact_phone_number
            validated_data["ifrc_emergency_name"] = dref.ifrc_emergency_name
            validated_data["ifrc_emergency_title"] = dref.ifrc_emergency_title
            validated_data["ifrc_emergency_phone_number"] = dref.ifrc_emergency_phone_number
            validated_data["ifrc_emergency_email"] = dref.ifrc_emergency_email
            validated_data["ifrc"] = dref.ifrc
            validated_data["icrc"] = dref.icrc
            validated_data["partner_national_society"] = dref.partner_national_society
            validated_data["government_requested_assistance"] = dref.government_requested_assistance
            validated_data["national_authorities"] = dref.national_authorities
            validated_data["un_or_other_actor"] = dref.un_or_other_actor
            validated_data["major_coordination_mechanism"] = dref.major_coordination_mechanism
            validated_data["people_assisted"] = dref.people_assisted
            validated_data["selection_criteria"] = dref.selection_criteria
            validated_data["entity_affected"] = dref.entity_affected
            validated_data["women"] = dref.women
            validated_data["men"] = dref.men
            validated_data["girls"] = dref.girls
            validated_data["boys"] = dref.boys
            validated_data["disability_people_per"] = dref.disability_people_per
            validated_data["people_per_urban"] = dref.people_per_urban
            validated_data["people_per_local"] = dref.people_per_local
            validated_data["people_targeted_with_early_actions"] = dref.people_targeted_with_early_actions
            validated_data["displaced_people"] = dref.displaced_people
            validated_data["operation_objective"] = dref.operation_objective
            validated_data["response_strategy"] = dref.response_strategy
            validated_data["created_by"] = self.context["request"].user
            validated_data["event_description"] = dref.event_description
            validated_data["anticipatory_actions"] = dref.anticipatory_actions
            validated_data["event_scope"] = dref.event_scope
            validated_data["assessment_report"] = dref.assessment_report
            validated_data["country"] = dref.country
            validated_data["risk_security_concern"] = dref.risk_security_concern
            validated_data["total_targeted_population"] = dref.total_targeted_population
            validated_data["is_there_major_coordination_mechanism"] = dref.is_there_major_coordination_mechanism
            validated_data["event_date"] = dref.event_date
            validated_data["people_in_need"] = dref.people_in_need
            validated_data["event_text"] = dref.event_text
            validated_data["ns_respond_date"] = dref.ns_respond_date

            if validated_data["type_of_dref"] == Dref.DrefType.LOAN:
                raise serializers.ValidationError(gettext("Can't create final report for dref type %s" % Dref.DrefType.LOAN))
            dref_final_report = super().create(validated_data)
            # XXX: Copy files from DREF (Only nested serialized fields)
            nested_serialized_file_fields = [
                "cover_image",
                "event_map",
            ]
            for file_field in nested_serialized_file_fields:
                dref_file = getattr(dref, file_field, None)
                if dref_file:
                    setattr(dref_final_report, file_field, dref_file.clone(self.context["request"].user))
            dref_final_report.save(update_fields=nested_serialized_file_fields)
            dref_final_report.planned_interventions.add(*dref.planned_interventions.all())
            dref_final_report.needs_identified.add(*dref.needs_identified.all())
            dref_final_report.district.add(*dref.district.all())
            dref_final_report.images.add(*dref.images.all())
            dref_final_report.risk_security.add(*dref.risk_security.all())
            dref_final_report.users.add(*dref.users.all())
            dref_final_report.national_society_actions.add(*dref.national_society_actions.all())
            # also update is_final_report_created for dref
            dref.is_final_report_created = True
            dref.save(update_fields=["is_final_report_created"])
        return dref_final_report

    def update(self, instance, validated_data):
        modified_at = validated_data.pop("modified_at", None)
        if modified_at is None:
            raise serializers.ValidationError({"modified_at": "Modified At is required!"})
        if modified_at and instance.modified_at and modified_at < instance.modified_at:
            raise serializers.ValidationError({"modified_at": settings.DREF_OP_UPDATE_FINAL_REPORT_UPDATE_ERROR_MESSAGE})

        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class CompletedDrefOperationsSerializer(serializers.ModelSerializer):
    country_details = MiniCountrySerializer(source="country", read_only=True)
    dref = MiniDrefSerializer(read_only=True)

    class Meta:
        model = DrefFinalReport
        fields = (
            "id",
            "created_at",
            "title",
            "appeal_code",
            "glide_code",
            "country",
            "date_of_publication",
            "country_details",
            "dref",
        )


class AddDrefUserSerializer(serializers.Serializer):
    users = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    final_report = serializers.IntegerField(write_only=True)

    def save(self):
        users_list = self.validated_data['users']
        final_report = self.validated_data['final_report']

        users = [User.objects.get(id=user_id) for user_id in users_list]
        # get the final_report and add the users_list to user
        final_report = DrefFinalReport.objects.filter(id=final_report).first()
        final_report.users.set(users)

        # lets also add to the dref as well
        dref = Dref.objects.filter(dreffinalreport=final_report.id).first()
        dref.users.set(users)

        # lets also add to operational update as well
        op_updates = DrefOperationalUpdate.objects.filter(dref=dref.id)
        for op in op_updates:
            op.users.set(users)
