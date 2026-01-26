import datetime
import os
from typing import List, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import get_language, gettext
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from api.models import Appeal
from api.serializers import (
    DisasterTypeSerializer,
    MiniCountrySerializer,
    MiniDistrictSerializer,
    UserNameSerializer,
)
from deployments.models import Sector
from dref.models import (
    Dref,
    DrefFile,
    DrefFinalReport,
    DrefOperationalUpdate,
    IdentifiedNeed,
    NationalSocietyAction,
    PlannedIntervention,
    PlannedInterventionIndicators,
    ProposedAction,
    ProposedActionActivities,
    RiskSecurity,
    SourceInformation,
)
from dref.utils import get_dref_users
from lang.serializers import ModelSerializer
from main.writable_nested_serializers import NestedCreateMixin, NestedUpdateMixin
from utils.file_check import validate_file_type

from .tasks import _translate_related_objects, send_dref_email


class RiskSecuritySerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = RiskSecurity
        fields = "__all__"


class SourceInformationSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = SourceInformation
        fields = "__all__"


class PlannedInterventionIndicatorsSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = PlannedInterventionIndicators
        fields = "__all__"


class ProposedActionActivitySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    sector = serializers.PrimaryKeyRelatedField(queryset=Sector.objects.all(), required=True)

    class Meta:
        model = ProposedActionActivities
        fields = "__all__"


class ProposedActionSerializer(NestedCreateMixin, NestedUpdateMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    proposed_type_display = serializers.CharField(source="get_proposed_type_display", read_only=True)
    activities = ProposedActionActivitySerializer(many=True, required=True)
    total_budget = serializers.IntegerField(required=True)

    class Meta:
        model = ProposedAction
        fields = "__all__"

    def validate_activities(self, activities):
        if not activities:
            raise serializers.ValidationError("At least one activity is required")
        return activities


class DrefFileInputSerializer(serializers.Serializer):
    file = serializers.ListField(child=serializers.FileField())


class DrefFileSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)
    created_by_details = UserNameSerializer(source="created_by", read_only=True)
    file = serializers.FileField(required=False)

    class Meta:
        model = DrefFile
        fields = "__all__"
        read_only_fields = ("created_by",)

    def validate_file(self, file):
        validate_file_type(file)
        return file

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        # XXX: 'caption' is a dynamically added field and not part of the model's declared fields.
        # Therefore, it can't be defined as a class attribute in the serializer.
        # We override it here to specify a custom max_length and make it optional.
        fields["caption"] = serializers.CharField(required=False, max_length=80, label=_("Caption"), allow_null=True)
        return fields

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class MiniOperationalUpdateActiveSerializer(serializers.ModelSerializer):
    type_of_onset_display = serializers.CharField(source="get_type_of_onset_display", read_only=True)
    disaster_category_display = serializers.CharField(source="get_disaster_category_display", read_only=True)
    type_of_dref_display = serializers.CharField(source="get_type_of_dref_display", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)
    application_type = serializers.SerializerMethodField()
    application_type_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

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
            "country_details",
            "application_type",
            "application_type_display",
            "status",
            "status_display",
            "date_of_approval",
        ]

    def get_application_type(self, obj) -> str:
        return "OPS_UPDATE"

    def get_application_type_display(self, obj) -> str:
        op_number = obj.operational_update_number
        return f"Operational update #{op_number}"


class MiniDrefFinalReportActiveSerializer(serializers.ModelSerializer):
    type_of_dref_display = serializers.CharField(source="get_type_of_dref_display", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)
    application_type = serializers.SerializerMethodField()
    application_type_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = DrefFinalReport
        fields = [
            "id",
            "title",
            "national_society",
            "disaster_type",
            "type_of_dref",
            "type_of_dref_display",
            "appeal_code",
            "created_at",
            "country",
            "country_details",
            "application_type",
            "application_type_display",
            "status",
            "status_display",
            "date_of_approval",
        ]

    def get_application_type(self, obj) -> str:
        return "FINAL_REPORT"

    def get_application_type_display(self, obj) -> str:
        return "Final report"


class MiniDrefSerializer(serializers.ModelSerializer):
    type_of_onset_display = serializers.CharField(source="get_type_of_onset_display", read_only=True)
    disaster_category_display = serializers.CharField(source="get_disaster_category_display", read_only=True)
    type_of_dref_display = serializers.CharField(source="get_type_of_dref_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)
    has_ops_update = serializers.SerializerMethodField()
    has_final_report = serializers.SerializerMethodField()
    application_type = serializers.SerializerMethodField()
    application_type_display = serializers.SerializerMethodField()
    unpublished_op_update_count = serializers.SerializerMethodField()
    unpublished_final_report_count = serializers.SerializerMethodField()
    operational_update_details = serializers.SerializerMethodField()
    final_report_details = serializers.SerializerMethodField()
    starting_language = serializers.CharField(read_only=True)

    class Meta:
        model = Dref
        fields = [
            "id",
            "title",
            "is_dref_imminent_v2",
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
            "country_details",
            "has_ops_update",
            "has_final_report",
            "application_type",
            "application_type_display",
            "unpublished_op_update_count",
            "unpublished_final_report_count",
            "status",
            "status_display",
            "date_of_approval",
            "starting_language",
        ]

    @extend_schema_field(MiniOperationalUpdateActiveSerializer(many=True))
    def get_operational_update_details(self, obj):
        queryset = DrefOperationalUpdate.objects.filter(dref_id=obj.id).order_by("-created_at")
        return MiniOperationalUpdateActiveSerializer(queryset, many=True).data

    @extend_schema_field(MiniDrefFinalReportActiveSerializer)
    def get_final_report_details(self, obj):
        queryset = DrefFinalReport.objects.filter(dref_id=obj.id).first()
        return MiniDrefFinalReportActiveSerializer(queryset).data

    def get_has_ops_update(self, obj) -> bool:
        op_count_count = obj.drefoperationalupdate_set.count()
        if op_count_count > 0:
            return True
        return False

    def get_has_final_report(self, obj) -> bool:
        if hasattr(obj, "dreffinalreport"):
            return True
        return False

    def get_application_type(self, obj) -> str:
        return "DREF"

    def get_application_type_display(self, obj) -> str:
        return "DREF application"

    def get_unpublished_op_update_count(self, obj) -> int:
        return DrefOperationalUpdate.objects.filter(dref_id=obj.id).exclude(status=Dref.Status.APPROVED).count()

    def get_unpublished_final_report_count(self, obj) -> int:
        return DrefFinalReport.objects.filter(dref_id=obj.id).exclude(status=Dref.Status.APPROVED).count()


class PlannedInterventionSerializer(
    NestedCreateMixin,
    NestedUpdateMixin,
    ModelSerializer,
):
    # budget_file_details = DrefFileSerializer(source="budget_file", read_only=True)
    id = serializers.IntegerField(required=False)
    image_url = serializers.SerializerMethodField()
    indicators = PlannedInterventionIndicatorsSerializer(many=True, required=False)
    title_display = serializers.CharField(source="get_title_display", read_only=True)

    class Meta:
        model = PlannedIntervention
        fields = "__all__"

    def get_image_url(self, plannedintervention) -> str:
        title = plannedintervention.title
        if title and self.context and "request" in self.context:
            request = self.context["request"]
            return PlannedIntervention.get_image_map(title, request)
        return None


class NationalSocietyActionSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)
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

    def get_image_url(self, nationalsocietyactions) -> str:
        title = nationalsocietyactions.title
        if title and self.context and "request" in self.context:
            request = self.context["request"]
            return NationalSocietyAction.get_image_map(title, request)
        return None


class IdentifiedNeedSerializer(ModelSerializer):
    id = serializers.IntegerField(required=False)
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

    def get_image_url(self, identifiedneed) -> str:
        title = identifiedneed.title
        if title and self.context and "request" in self.context:
            request = self.context["request"]
            return IdentifiedNeed.get_image_map(title, request)
        return None


class MiniOperationalUpdateSerializer(ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = DrefOperationalUpdate
        fields = [
            "id",
            "title",
            "operational_update_number",
            "status",
            "status_display",
        ]


class MiniDrefFinalReportSerializer(ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = DrefFinalReport
        fields = [
            "id",
            "title",
            "status",
            "status_display",
        ]


class DrefSerializer(NestedUpdateMixin, NestedCreateMixin, ModelSerializer):
    SUB_TOTAL_COST = 75000
    SURGE_DEPLOYMENT_COST = 10000
    SURGE_INDIRECT_COST = 5800
    NO_SURGE_INDIRECT_COST = 5000
    MAX_NUMBER_OF_IMAGES = 4
    ALLOWED_BUDGET_FILE_EXTENSIONS = ["pdf"]
    ALLOWED_ASSESSMENT_REPORT_EXTENSIONS = ["pdf", "docx", "pptx", "xlsx"]
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
    disaster_category_analysis_details = DrefFileSerializer(
        source="disaster_category_analysis", read_only=True, required=False, allow_null=True
    )
    targeting_strategy_support_file_details = DrefFileSerializer(
        source="targeting_strategy_support_file", read_only=True, required=False, allow_null=True
    )
    images_file = DrefFileSerializer(many=True, required=False, allow_null=True, source="images")
    # field_report_details = MiniFieldReportSerializer(source='field_report', read_only=True)
    created_by_details = UserNameSerializer(source="created_by", read_only=True)
    users_details = UserNameSerializer(source="users", many=True, read_only=True)
    budget_file_details = DrefFileSerializer(source="budget_file", read_only=True)
    cover_image_file = DrefFileSerializer(source="cover_image", required=False, allow_null=True)
    disaster_type_details = DisasterTypeSerializer(source="disaster_type", read_only=True)
    operational_update_details = MiniOperationalUpdateSerializer(source="drefoperationalupdate_set", many=True, read_only=True)
    final_report_details = MiniDrefFinalReportSerializer(source="dreffinalreport", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)
    district_details = MiniDistrictSerializer(source="district", read_only=True, many=True)
    assessment_report_details = DrefFileSerializer(source="assessment_report", read_only=True)
    supporting_document_details = DrefFileSerializer(
        source="supporting_document", read_only=True, required=False, allow_null=True
    )
    risk_security = RiskSecuritySerializer(many=True, required=False)
    modified_at = serializers.DateTimeField(required=False)
    dref_access_user_list = serializers.SerializerMethodField()
    source_information = SourceInformationSerializer(many=True, required=False)
    scenario_analysis_supporting_document_details = DrefFileSerializer(
        source="scenario_analysis_supporting_document", read_only=True, required=False, allow_null=True
    )
    contingency_plans_supporting_document_details = DrefFileSerializer(
        source="contingency_plans_supporting_document", read_only=True, required=False, allow_null=True
    )
    proposed_action = ProposedActionSerializer(many=True, required=False)

    class Meta:
        model = Dref
        read_only_fields = (
            "modified_by",
            "created_by",
            "budget_file_preview",
            "is_dref_imminent_v2",
            "starting_language",
        )
        exclude = (
            "cover_image",
            "event_map",
            "images",
            "users",
        )

    def get_dref_access_user_list(self, obj) -> List[int] | None:
        dref_users_list = get_dref_users()
        for dref in dref_users_list:
            if obj.id == dref["id"]:
                return dref["users"]
        return

    # def to_representation(self, instance):
    #     def _remove_digits_after_decimal(value) -> float:
    #         # NOTE: We are doing this to remove decimal after 3 digits whole numbers
    #         # eg: 100.00% be replaced with 100%
    #         if value and len(value) == 3:
    #             return value.split(".")[0]
    #         return value

    #     data = super().to_representation(instance)
    #     for key in [
    #         "disability_people_per",
    #         "people_per_urban",
    #         "people_per_local",
    #     ]:
    #         value = data.get(key) or ""
    #         data[key] = _remove_digits_after_decimal(value)
    #     return data

    def validate(self, data):
        event_date = data.get("event_date")
        operation_timeframe = data.get("operation_timeframe")
        if self.instance and self.instance.status == Dref.Status.FINALIZING:
            raise serializers.ValidationError(gettext("Cannot be updated while the translation is in progress"))
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
        if self.instance and self.instance.status == Dref.Status.APPROVED:
            raise serializers.ValidationError("Approved Dref can't be changed. Please contact Admin")
        if self.instance and DrefFinalReport.objects.filter(dref=self.instance, status=Dref.Status.APPROVED).exists():
            raise serializers.ValidationError(gettext("Can't Update dref for approved Final Report"))
        if operation_timeframe and is_assessment_report and operation_timeframe > 30:
            raise serializers.ValidationError(
                gettext("Operation timeframe can't be greater than %s for assessment_report" % self.MAX_OPERATION_TIMEFRAME)
            )

        # NOTE: Validation for type DREF Imminent
        if data.get("type_of_dref") == Dref.DrefType.IMMINENT:
            is_surge_personnel_deployed = data.get("is_surge_personnel_deployed")
            sub_total_cost = data.get("sub_total_cost")
            surge_deployment_cost = data.get("surge_deployment_cost")
            indirect_cost = data.get("indirect_cost")
            total_cost = data.get("total_cost")
            proposed_actions = data.get("proposed_action", [])

            if not proposed_actions:
                raise serializers.ValidationError(
                    {"proposed_action": gettext("Proposed Action is required for type DREF Imminent")}
                )
            if not sub_total_cost:
                raise serializers.ValidationError({"sub_total_cost": gettext("Sub-total is required for Imminent DREF")})
            if sub_total_cost != self.SUB_TOTAL_COST:
                raise serializers.ValidationError(
                    {"sub_total": gettext("Sub-total should be equal to %s for Imminent DREF" % self.SUB_TOTAL_COST)}
                )
            if is_surge_personnel_deployed and not surge_deployment_cost:
                raise serializers.ValidationError(
                    {"surge_deployment_cost": gettext("Surge Deployment is required for Imminent DREF")}
                )
            if not indirect_cost:
                raise serializers.ValidationError({"indirect_cost": gettext("Indirect Cost is required for Imminent DREF")})
            if not total_cost:
                raise serializers.ValidationError({"total_cost": gettext("Total is required for Imminent DREF")})

            total_proposed_budget = sum(action.get("total_budget", 0) for action in proposed_actions)
            if total_proposed_budget != sub_total_cost:
                raise serializers.ValidationError("Sub-total should be equal to proposed budget")

            if is_surge_personnel_deployed:
                if surge_deployment_cost != self.SURGE_DEPLOYMENT_COST:
                    raise serializers.ValidationError(
                        {
                            "surge_deployment_cost": gettext(
                                "Surge Deployment Cost should be equal to %s for Surge Personnel Deployed"
                                % self.SURGE_DEPLOYMENT_COST
                            )
                        }
                    )
                if indirect_cost != self.SURGE_INDIRECT_COST:
                    raise serializers.ValidationError(
                        {
                            "indirect_cost": gettext(
                                "Indirect Cost should be equal to %s for Surge Personnel Deployed" % self.SURGE_INDIRECT_COST
                            )
                        }
                    )
                expected_total = surge_deployment_cost + indirect_cost + sub_total_cost
            else:
                if indirect_cost != self.NO_SURGE_INDIRECT_COST:
                    raise serializers.ValidationError(
                        {
                            "indirect_cost": gettext(
                                "Indirect Cost should be equal to %s for No Surge Personnel Deployed"
                                % self.NO_SURGE_INDIRECT_COST
                            )
                        }
                    )
                expected_total = indirect_cost + sub_total_cost

            if expected_total != total_cost:
                raise serializers.ValidationError(
                    {"total_cost": gettext("Total should be equal to sum of Sub-total, Surge Deployment Cost and Indirect Cost")}
                )
        return data

    def validate_images_file(self, images):
        # Don't allow images more than MAX_NUMBER_OF_IMAGES
        if len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(gettext("Can add utmost %s images" % self.MAX_NUMBER_OF_IMAGES))
        images_id = [image["id"] for image in images]
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
                    "Only image owner can attach image. Not allowed image ids: %s" % ",".join(map(str, images_id_without_access))
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

    def validate_budget_file_preview(self, budget_file_preview):
        validate_file_type(budget_file_preview)
        return budget_file_preview

    def create(self, validated_data):
        current_language = get_language()
        validated_data["starting_language"] = current_language
        validated_data["created_by"] = self.context["request"].user
        validated_data["is_active"] = True
        type_of_dref = validated_data.get("type_of_dref")
        if type_of_dref and type_of_dref == Dref.DrefType.ASSESSMENT:
            # Previous Operations
            validated_data["lessons_learned"] = None
            validated_data["complete_child_safeguarding_risk"] = None
            validated_data["child_safeguarding_risk_level"] = None
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
        # NOTE: Setting flag for only newly created DREF of type IMMINENT
        if type_of_dref == Dref.DrefType.IMMINENT:
            validated_data["is_dref_imminent_v2"] = True

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
            validated_data["complete_child_safeguarding_risk"] = None
            validated_data["child_safeguarding_risk_level"] = None
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
        validated_data["modified_at"] = timezone.now()
        dref = super().update(instance, validated_data)
        if to:
            transaction.on_commit(lambda: send_dref_email.delay(dref.id, list(to), "Updated"))
        return dref


class DrefOperationalUpdateSerializer(NestedUpdateMixin, NestedCreateMixin, ModelSerializer):
    MAX_NUMBER_OF_IMAGES = 4
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
    source_information = SourceInformationSerializer(many=True, required=False)

    class Meta:
        model = DrefOperationalUpdate
        read_only_fields = (
            "operational_update_number",
            "modified_by",
            "created_by",
        )
        exclude = (
            "images",
            "photos",
            "event_map",
            "cover_image",
            "users",
        )

    def validate(self, data):
        dref = data.get("dref")
        if self.instance and self.instance.status == Dref.Status.FINALIZING:
            raise serializers.ValidationError(gettext("Cannot be updated while the translation is in progress"))
        if not self.instance and dref:
            if dref.status != Dref.Status.APPROVED:
                raise serializers.ValidationError(gettext("Can't create Operational Update for not approved dref."))
            # get the latest dref_operation_update and
            # check whether it is published or not, exclude no operational object created so far
            dref_operational_update = (
                DrefOperationalUpdate.objects.filter(dref=dref).order_by("-operational_update_number").first()
            )
            if dref_operational_update and dref_operational_update.status != Dref.Status.APPROVED:
                raise serializers.ValidationError(
                    gettext(
                        "Can't create Operational Update for not \
                        approved Operational Update %s id and Operational Update Number %i."
                        % (dref_operational_update.id, dref_operational_update.operational_update_number)
                    )
                )

        return data

    def validate_appeal_code(self, appeal_code):
        if appeal_code and appeal_code != self.instance.appeal_code:
            raise serializers.ValidationError("Can't edit MDR Code")
        return appeal_code

    def get_total_timeframe(self, start_date, end_date):
        if start_date and end_date:
            start_date_month = datetime.datetime.strftime("%m")
            end_date_month = datetime.datetime.strptime("%m")
            return abs(end_date_month - start_date_month)
        return None

    def validate_budget_file_preview(self, budget_file_preview):
        validate_file_type(budget_file_preview)
        return budget_file_preview

    def validate_images_file(self, images):
        if images and len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError("Can add utmost %s images" % self.MAX_NUMBER_OF_IMAGES)
        return images

    def create(self, validated_data):
        dref = validated_data["dref"]
        current_language = get_language()
        starting_langauge = validated_data.get("starting_language")
        valid_languages = [dref.starting_language, dref.translation_module_original_language]
        if current_language != starting_langauge:
            raise serializers.ValidationError(gettext("Starting language does not match the expected language."))
        if starting_langauge not in valid_languages:
            raise serializers.ValidationError(
                gettext(f"Invalid starting language. Supported options are '{valid_languages[0]}' and '{valid_languages[1]}'.")
            )
        dref_operational_update = DrefOperationalUpdate.objects.filter(dref=dref).order_by("-operational_update_number").first()
        validated_data["created_by"] = self.context["request"].user
        if not dref_operational_update:
            validated_data["title"] = dref.title
            validated_data["title_prefix"] = dref.title_prefix
            validated_data["national_society"] = dref.national_society
            validated_data["disaster_type"] = dref.disaster_type
            validated_data["type_of_onset"] = dref.type_of_onset
            # NOTE: Change the type_of_dref to RESPONSE if it is newly created DREF IMMINENT
            validated_data["type_of_dref"] = (
                Dref.DrefType.RESPONSE
                if dref.type_of_dref == Dref.DrefType.IMMINENT and dref.is_dref_imminent_v2
                else dref.type_of_dref
            )
            validated_data["disaster_category"] = dref.disaster_category
            validated_data["number_of_people_targeted"] = dref.num_assisted
            validated_data["number_of_people_affected"] = dref.num_affected
            validated_data["estimated_number_of_affected_male"] = dref.estimated_number_of_affected_male
            validated_data["estimated_number_of_affected_female"] = dref.estimated_number_of_affected_female
            validated_data["estimated_number_of_affected_girls_under_18"] = dref.estimated_number_of_affected_girls_under_18
            validated_data["estimated_number_of_affected_boys_under_18"] = dref.estimated_number_of_affected_boys_under_18
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
            validated_data["national_society_integrity_contact_name"] = dref.national_society_integrity_contact_name
            validated_data["national_society_integrity_contact_email"] = dref.national_society_integrity_contact_email
            validated_data["national_society_integrity_contact_title"] = dref.national_society_integrity_contact_title
            validated_data["national_society_integrity_contact_phone_number"] = (
                dref.national_society_integrity_contact_phone_number
            )
            validated_data["national_society_hotline_phone_number"] = dref.national_society_hotline_phone_number
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
            validated_data["new_operational_end_date"] = dref.end_date
            validated_data["operational_update_number"] = 1  # if no any dref operational update created so far
            validated_data["dref_allocated_so_far"] = dref.amount_requested
            validated_data["total_dref_allocation"] = dref.amount_requested
            if dref.type_of_dref == Dref.DrefType.IMMINENT:
                validated_data["dref_allocated_so_far"] = dref.total_cost
                validated_data["total_dref_allocation"] = dref.total_cost
                # NOTE:These field should be blank for operational update
                validated_data["total_operation_timeframe"] = None
                validated_data["new_operational_end_date"] = None
            validated_data["event_description"] = dref.event_description
            validated_data["anticipatory_actions"] = dref.anticipatory_actions
            validated_data["event_scope"] = dref.event_scope
            validated_data["budget_file"] = dref.budget_file
            validated_data["country"] = dref.country
            validated_data["risk_security_concern"] = dref.risk_security_concern
            validated_data["has_anti_fraud_corruption_policy"] = dref.has_anti_fraud_corruption_policy
            validated_data["has_sexual_abuse_policy"] = dref.has_sexual_abuse_policy
            validated_data["has_child_protection_policy"] = dref.has_child_protection_policy
            validated_data["has_whistleblower_protection_policy"] = dref.has_whistleblower_protection_policy
            validated_data["has_anti_sexual_harassment_policy"] = dref.has_anti_sexual_harassment_policy
            validated_data["has_child_safeguarding_risk_analysis_assessment"] = (
                dref.has_child_safeguarding_risk_analysis_assessment
            )
            validated_data["event_date"] = dref.event_date
            validated_data["ns_respond_date"] = dref.ns_respond_date
            validated_data["did_ns_respond"] = dref.did_ns_respond
            validated_data["total_targeted_population"] = dref.total_targeted_population
            validated_data["is_there_major_coordination_mechanism"] = dref.is_there_major_coordination_mechanism
            validated_data["human_resource"] = dref.human_resource
            validated_data["is_volunteer_team_diverse"] = dref.is_volunteer_team_diverse
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
            validated_data["identified_gaps"] = dref.identified_gaps
            validated_data["is_man_made_event"] = dref.is_man_made_event
            validated_data["event_text"] = dref.event_text
            validated_data["did_national_society"] = dref.did_national_society
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
            operational_update.source_information.add(*dref.source_information.all())
        else:
            # get the latest dref operational update
            validated_data["title"] = dref_operational_update.title
            validated_data["title_prefix"] = dref_operational_update.title_prefix
            validated_data["national_society"] = dref_operational_update.national_society
            validated_data["disaster_type"] = dref_operational_update.disaster_type
            validated_data["type_of_onset"] = dref_operational_update.type_of_onset
            # NOTE: Change the type_of_dref for OpsUpdate to RESPONSE if it is newly created DREF IMMINENT
            validated_data["type_of_dref"] = (
                Dref.DrefType.RESPONSE
                if dref.type_of_dref == Dref.DrefType.IMMINENT and dref.is_dref_imminent_v2
                else dref.type_of_dref
            )
            validated_data["disaster_category"] = dref_operational_update.disaster_category
            validated_data["number_of_people_targeted"] = dref_operational_update.number_of_people_targeted
            validated_data["number_of_people_affected"] = dref_operational_update.number_of_people_affected
            validated_data["emergency_appeal_planned"] = dref_operational_update.emergency_appeal_planned
            validated_data["appeal_code"] = dref_operational_update.appeal_code
            validated_data["glide_code"] = dref_operational_update.glide_code
            validated_data["total_dref_allocation"] = dref_operational_update.total_dref_allocation
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
            validated_data["national_society_contact_phone_number"] = (
                dref_operational_update.national_society_contact_phone_number
            )
            validated_data["national_society_integrity_contact_name"] = (
                dref_operational_update.national_society_integrity_contact_name
            )
            validated_data["national_society_integrity_contact_email"] = (
                dref_operational_update.national_society_integrity_contact_email
            )
            validated_data["national_society_integrity_contact_title"] = (
                dref_operational_update.national_society_integrity_contact_title
            )
            validated_data["national_society_integrity_contact_phone_number"] = (
                dref_operational_update.national_society_integrity_contact_phone_number
            )
            validated_data["national_society_hotline_phone_number"] = (
                dref_operational_update.national_society_hotline_phone_number
            )
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
            validated_data["new_operational_end_date"] = dref_operational_update.new_operational_end_date
            validated_data["dref_allocated_so_far"] = dref_operational_update.total_dref_allocation
            validated_data["event_description"] = dref_operational_update.event_description
            validated_data["anticipatory_actions"] = dref_operational_update.anticipatory_actions
            validated_data["event_scope"] = dref_operational_update.event_scope
            validated_data["budget_file"] = dref_operational_update.budget_file
            validated_data["assessment_report"] = dref_operational_update.assessment_report
            validated_data["country"] = dref_operational_update.country
            validated_data["risk_security_concern"] = dref_operational_update.risk_security_concern
            validated_data["has_anti_fraud_corruption_policy"] = dref_operational_update.has_anti_fraud_corruption_policy
            validated_data["has_sexual_abuse_policy"] = dref_operational_update.has_sexual_abuse_policy
            validated_data["has_child_protection_policy"] = dref_operational_update.has_child_protection_policy
            validated_data["has_whistleblower_protection_policy"] = dref_operational_update.has_whistleblower_protection_policy
            validated_data["has_anti_sexual_harassment_policy"] = dref_operational_update.has_anti_sexual_harassment_policy
            validated_data["has_child_safeguarding_risk_analysis_assessment"] = (
                dref_operational_update.has_child_safeguarding_risk_analysis_assessment
            )
            validated_data["event_date"] = dref_operational_update.event_date
            validated_data["ns_respond_date"] = dref_operational_update.ns_respond_date
            validated_data["did_ns_respond"] = dref_operational_update.did_ns_respond
            validated_data["total_targeted_population"] = dref_operational_update.total_targeted_population
            validated_data["is_there_major_coordination_mechanism"] = (
                dref_operational_update.is_there_major_coordination_mechanism
            )
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
            validated_data["identified_gaps"] = dref_operational_update.identified_gaps
            validated_data["is_man_made_event"] = dref_operational_update.is_man_made_event
            validated_data["event_text"] = dref_operational_update.event_text
            validated_data["did_national_society"] = dref_operational_update.did_national_society
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
            operational_update.source_information.add(*dref_operational_update.source_information.all())

        # NOTE: Sync related models with the starting language
        if starting_langauge != "en":
            _translate_related_objects(
                instance=operational_update,
                auto_translate=False,
                language=starting_langauge,
            )
        return operational_update

    def update(self, instance, validated_data):
        validated_data["modified_by"] = self.context["request"].user
        modified_at = validated_data.pop("modified_at", None)
        if modified_at is None:
            raise serializers.ValidationError({"modified_at": "Modified At is required!"})

        if modified_at and instance.modified_at and modified_at < instance.modified_at:
            raise serializers.ValidationError({"modified_at": settings.DREF_OP_UPDATE_FINAL_REPORT_UPDATE_ERROR_MESSAGE})
        validated_data["modified_at"] = timezone.now()
        return super().update(instance, validated_data)


class DrefFinalReportSerializer(NestedUpdateMixin, NestedCreateMixin, ModelSerializer):
    MAX_NUMBER_OF_PHOTOS = 4
    SUB_TOTAL_COST = 75000
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
    modified_by_details = UserNameSerializer(source="modified_by", read_only=True)
    disaster_type_details = DisasterTypeSerializer(source="disaster_type", read_only=True)
    source_information = SourceInformationSerializer(many=True, required=False)
    proposed_action = ProposedActionSerializer(many=True, required=False)

    class Meta:
        model = DrefFinalReport
        read_only_fields = (
            "modified_by",
            "created_by",
            "financial_report_preview",
            "is_dref_imminent_v2",
        )
        exclude = (
            "images",
            "photos",
            "event_map",
            "cover_image",
            "users",
        )

    def validate(self, data):
        dref = data.get("dref")
        if self.instance and self.instance.status == Dref.Status.FINALIZING:
            raise serializers.ValidationError(gettext("Cannot be updated while the translation is in progress"))
        # Check if dref is published and operational_update associated with it is also published
        if not self.instance and dref:
            if dref.status != Dref.Status.APPROVED:
                raise serializers.ValidationError(gettext("Can't create Final Report for not approved dref."))
            dref_operational_update = (
                DrefOperationalUpdate.objects.filter(dref=dref).exclude(status=Dref.Status.APPROVED).values_list("id", flat=True)
            )
            if dref_operational_update:
                raise serializers.ValidationError(
                    gettext(
                        "Can't create Final Report for not approved Operational Update %s ids "
                        % ",".join(map(str, dref_operational_update))
                    )
                )

        if self.instance and self.instance.status == Dref.Status.APPROVED:
            raise serializers.ValidationError(gettext("Can't update approved final report."))

        # NOTE: Validation for type DREF Imminent
        if self.instance and self.instance.is_dref_imminent_v2 and data.get("type_of_dref") == Dref.DrefType.IMMINENT:
            sub_total_cost = data.get("sub_total_cost")
            sub_total_expenditure_cost = data.get("sub_total_expenditure_cost")
            surge_deployment_expenditure_cost = data.get("surge_deployment_expenditure_cost") or 0
            indirect_cost = data.get("indirect_cost")
            indirect_expenditure_cost = data.get("indirect_expenditure_cost")
            total_cost = data.get("total_cost")
            total_expenditure_cost = data.get("total_expenditure_cost")
            proposed_actions = data.get("proposed_action", [])

            if not proposed_actions:
                raise serializers.ValidationError(
                    {"proposed_action": gettext("Proposed Action is required for type DREF Imminent")}
                )
            if not sub_total_cost:
                raise serializers.ValidationError({"sub_total_cost": gettext("Sub-total is required for Imminent DREF")})
            if not sub_total_expenditure_cost:
                raise serializers.ValidationError(
                    {"sub_total_expenditure_cost": gettext("Sub-total Expenditure is required for Imminent DREF")}
                )
            if sub_total_cost != self.SUB_TOTAL_COST:
                raise serializers.ValidationError(
                    {"sub_total": gettext("Sub-total should be equal to %s for Imminent DREF" % self.SUB_TOTAL_COST)}
                )
            if not indirect_cost:
                raise serializers.ValidationError({"indirect_cost": gettext("Indirect Cost is required for Imminent DREF")})
            if not indirect_expenditure_cost:
                raise serializers.ValidationError(
                    {"indirect_expenditure_cost": gettext("Indirect Expenditure is required for Imminent DREF")}
                )
            if not total_cost:
                raise serializers.ValidationError({"total_cost": gettext("Total is required for Imminent DREF")})
            if not total_expenditure_cost:
                raise serializers.ValidationError(
                    {"total_expenditure_cost": gettext("Total Expenditure is required for Imminent DREF")}
                )

            total_proposed_budget: int = 0
            total_proposed_expenditure: int = 0
            for action in proposed_actions:
                total_proposed_budget += action.get("total_budget", 0)
                total_proposed_expenditure += action.get("total_expenditure", 0)
            if total_proposed_budget != sub_total_cost:
                raise serializers.ValidationError({"sub_total_cost": gettext("Sub-total should be equal to proposed budget.")})
            if total_proposed_expenditure != sub_total_expenditure_cost:
                raise serializers.ValidationError(
                    {"sub_total_expenditure_cost": gettext("Sub-total Expenditure should be equal to proposed expenditure.")}
                )
            expected_total_expenditure_cost: int = (
                sub_total_expenditure_cost + surge_deployment_expenditure_cost + indirect_expenditure_cost
            )
            if expected_total_expenditure_cost != total_expenditure_cost:
                raise serializers.ValidationError(
                    {
                        "total_expenditure_cost": gettext(
                            "Total Expenditure Cost should be equal to sum of Sub-total Expenditure, "
                            "Surge Deployment Expenditure and Indirect Expenditure Cost."
                        )
                    }
                )
        return data

    def validate_photos(self, photos):
        if photos and len(photos) > self.MAX_NUMBER_OF_PHOTOS:
            raise serializers.ValidationError("Can add utmost %s photos" % self.MAX_NUMBER_OF_PHOTOS)
        return photos

    def validate_images_file(self, images):
        if images and len(images) > self.MAX_NUMBER_OF_PHOTOS:
            raise serializers.ValidationError("Can add utmost %s images" % self.MAX_NUMBER_OF_PHOTOS)
        return images

    def validate_financial_report_preview(self, financial_report_preview):
        validate_file_type(financial_report_preview)
        return financial_report_preview

    def create(self, validated_data):
        # here check if there is operational update for corresponding dref
        # if yes copy from the latest operational update
        # else copy from dref
        dref = validated_data["dref"]
        current_language = get_language()
        starting_langauge = validated_data.get("starting_language")
        valid_languages = [dref.starting_language, dref.translation_module_original_language]
        if current_language != starting_langauge:
            raise serializers.ValidationError(gettext("Starting language does not match the expected language."))
        if starting_langauge not in valid_languages:
            raise serializers.ValidationError(
                gettext(f"Invalid starting language. Supported options are '{valid_languages[0]}' and '{valid_languages[1]}'.")
            )
        dref_operational_update = (
            DrefOperationalUpdate.objects.filter(dref=dref, status=Dref.Status.APPROVED)
            .order_by("-operational_update_number")
            .first()
        )
        validated_data["created_by"] = self.context["request"].user
        # NOTE: Checks and common fields for the new dref final reports of new dref imminents
        if dref.type_of_dref == Dref.DrefType.IMMINENT and dref.is_dref_imminent_v2:
            validated_data["is_dref_imminent_v2"] = True
            validated_data["sub_total_cost"] = dref.sub_total_cost
            validated_data["surge_deployment_cost"] = dref.surge_deployment_cost
            validated_data["surge_deployment_expenditure_cost"] = dref.surge_deployment_cost
            validated_data["indirect_cost"] = dref.indirect_cost
            validated_data["indirect_expenditure_cost"] = dref.indirect_cost
            validated_data["total_cost"] = dref.total_cost

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
            validated_data["estimated_number_of_affected_male"] = dref_operational_update.estimated_number_of_affected_male
            validated_data["estimated_number_of_affected_female"] = dref_operational_update.estimated_number_of_affected_female
            validated_data["estimated_number_of_affected_girls_under_18"] = dref.estimated_number_of_affected_girls_under_18
            validated_data["estimated_number_of_affected_boys_under_18"] = dref.estimated_number_of_affected_boys_under_18
            validated_data["total_dref_allocation"] = dref_operational_update.total_dref_allocation
            validated_data["total_operation_timeframe"] = dref_operational_update.total_operation_timeframe
            validated_data["operation_start_date"] = dref_operational_update.dref.date_of_approval
            validated_data["operation_end_date"] = dref_operational_update.new_operational_end_date
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
            validated_data["national_society_contact_phone_number"] = (
                dref_operational_update.national_society_contact_phone_number
            )
            validated_data["national_society_integrity_contact_name"] = (
                dref_operational_update.national_society_integrity_contact_name
            )
            validated_data["national_society_integrity_contact_email"] = (
                dref_operational_update.national_society_integrity_contact_email
            )
            validated_data["national_society_integrity_contact_title"] = (
                dref_operational_update.national_society_integrity_contact_title
            )
            validated_data["national_society_integrity_contact_phone_number"] = (
                dref_operational_update.national_society_integrity_contact_phone_number
            )
            validated_data["national_society_hotline_phone_number"] = (
                dref_operational_update.national_society_hotline_phone_number
            )
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
            validated_data["event_description"] = dref_operational_update.event_description
            validated_data["anticipatory_actions"] = dref_operational_update.anticipatory_actions
            validated_data["event_scope"] = dref_operational_update.event_scope
            validated_data["country"] = dref_operational_update.country
            validated_data["risk_security_concern"] = dref_operational_update.risk_security_concern
            validated_data["has_anti_fraud_corruption_policy"] = dref_operational_update.has_anti_fraud_corruption_policy
            validated_data["has_sexual_abuse_policy"] = dref_operational_update.has_sexual_abuse_policy
            validated_data["has_child_protection_policy"] = dref_operational_update.has_child_protection_policy
            validated_data["has_whistleblower_protection_policy"] = dref_operational_update.has_whistleblower_protection_policy
            validated_data["has_anti_sexual_harassment_policy"] = dref_operational_update.has_anti_sexual_harassment_policy
            validated_data["has_child_safeguarding_risk_analysis_assessment"] = (
                dref_operational_update.has_child_safeguarding_risk_analysis_assessment
            )
            validated_data["total_targeted_population"] = dref_operational_update.total_targeted_population
            validated_data["is_there_major_coordination_mechanism"] = (
                dref_operational_update.is_there_major_coordination_mechanism
            )
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
            dref_final_report.source_information.add(*dref_operational_update.source_information.all())
            if dref_final_report.is_dref_imminent_v2:
                dref_final_report.proposed_action.add(*dref.proposed_action.all())
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
            validated_data["estimated_number_of_affected_male"] = dref.estimated_number_of_affected_male
            validated_data["estimated_number_of_affected_female"] = dref.estimated_number_of_affected_female
            validated_data["estimated_number_of_affected_girls_under_18"] = dref.estimated_number_of_affected_girls_under_18
            validated_data["estimated_number_of_affected_boys_under_18"] = dref.estimated_number_of_affected_boys_under_18
            validated_data["total_operation_timeframe"] = dref.operation_timeframe
            validated_data["operation_start_date"] = dref.date_of_approval
            validated_data["operation_end_date"] = dref.end_date
            validated_data["appeal_code"] = dref.appeal_code
            validated_data["total_dref_allocation"] = dref.amount_requested
            if dref.type_of_dref == Dref.DrefType.IMMINENT:
                validated_data["total_dref_allocation"] = dref.total_cost
                # NOTE:These field should be blank for final report
                validated_data["total_operation_timeframe"] = None
                validated_data["total_operation_timeframe_imminent"] = dref.operation_timeframe_imminent
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
            validated_data["national_society_integrity_contact_name"] = dref.national_society_integrity_contact_name
            validated_data["national_society_integrity_contact_email"] = dref.national_society_integrity_contact_email
            validated_data["national_society_integrity_contact_title"] = dref.national_society_integrity_contact_title
            validated_data["national_society_integrity_contact_phone_number"] = (
                dref.national_society_integrity_contact_phone_number
            )
            validated_data["national_society_hotline_phone_number"] = dref.national_society_hotline_phone_number
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
            validated_data["event_description"] = dref.event_description
            validated_data["anticipatory_actions"] = dref.anticipatory_actions
            validated_data["event_scope"] = dref.event_scope
            validated_data["assessment_report"] = dref.assessment_report
            validated_data["country"] = dref.country
            validated_data["risk_security_concern"] = dref.risk_security_concern
            validated_data["has_anti_fraud_corruption_policy"] = dref.has_anti_fraud_corruption_policy
            validated_data["has_sexual_abuse_policy"] = dref.has_sexual_abuse_policy
            validated_data["has_child_protection_policy"] = dref.has_child_protection_policy
            validated_data["has_whistleblower_protection_policy"] = dref.has_whistleblower_protection_policy
            validated_data["has_anti_sexual_harassment_policy"] = dref.has_anti_sexual_harassment_policy
            validated_data["has_child_safeguarding_risk_analysis_assessment"] = (
                dref.has_child_safeguarding_risk_analysis_assessment
            )
            validated_data["total_targeted_population"] = dref.total_targeted_population
            validated_data["is_there_major_coordination_mechanism"] = dref.is_there_major_coordination_mechanism
            validated_data["event_date"] = dref.event_date
            validated_data["people_in_need"] = dref.people_in_need
            validated_data["event_text"] = dref.event_text
            validated_data["ns_respond_date"] = dref.ns_respond_date

            if validated_data["type_of_dref"] == Dref.DrefType.LOAN:
                raise serializers.ValidationError(
                    gettext("Can't create final report for dref type %s" % Dref.DrefType.LOAN.label)
                )

            # NOTE: Checks for the new dref final reports of new dref imminents
            if validated_data["type_of_dref"] == Dref.DrefType.IMMINENT and dref.is_dref_imminent_v2:
                validated_data["is_dref_imminent_v2"] = True
                validated_data["sub_total_cost"] = dref.sub_total_cost
                validated_data["surge_deployment_cost"] = dref.surge_deployment_cost
                validated_data["surge_deployment_expenditure_cost"] = dref.surge_deployment_cost
                validated_data["indirect_cost"] = dref.indirect_cost
                validated_data["indirect_expenditure_cost"] = dref.indirect_cost
                validated_data["total_cost"] = dref.total_cost

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
            dref_final_report.source_information.add(*dref.source_information.all())
            if dref_final_report.type_of_dref == Dref.DrefType.IMMINENT and dref_final_report.is_dref_imminent_v2:
                dref_final_report.proposed_action.add(*dref.proposed_action.all())
            # also update is_final_report_created for dref
            dref.is_final_report_created = True
            dref.save(update_fields=["is_final_report_created"])

        # NOTE: Sync related models with the starting language
        if starting_langauge != "en":
            _translate_related_objects(
                instance=dref_final_report,
                auto_translate=False,
                language=starting_langauge,
            )
        return dref_final_report

    def update(self, instance, validated_data):
        modified_at = validated_data.pop("modified_at", None)
        if modified_at is None:
            raise serializers.ValidationError({"modified_at": "Modified At is required!"})
        if modified_at and instance.modified_at and modified_at < instance.modified_at:
            raise serializers.ValidationError({"modified_at": settings.DREF_OP_UPDATE_FINAL_REPORT_UPDATE_ERROR_MESSAGE})
        validated_data["modified_at"] = timezone.now()
        validated_data["modified_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class CompletedDrefOperationsSerializer(serializers.ModelSerializer):
    country_details = MiniCountrySerializer(source="country", read_only=True)
    dref = MiniDrefSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    application_type = serializers.SerializerMethodField()
    application_type_display = serializers.SerializerMethodField()
    starting_language = serializers.CharField(read_only=True)

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
            "application_type",
            "application_type_display",
            "dref",
            "status",
            "status_display",
            "starting_language",
        )

    def get_application_type(self, obj) -> str:
        return "FINAL_REPORT"

    def get_application_type_display(self, obj) -> str:
        return "Final report"


class AddDrefUserSerializer(serializers.Serializer):
    users = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    dref = serializers.IntegerField(write_only=True)

    def save(self):
        users_list = self.validated_data["users"]
        dref = self.validated_data["dref"]

        users: List[User] = [User.objects.get(id=user_id) for user_id in users_list]

        # get the dref and add the users_list to user
        dref: Optional[Dref] = Dref.objects.filter(id=dref).first()
        unique_emails: set[str] = {
            user.email for user in users if user.email and user.email not in {t.email for t in dref.users.iterator()}
        }
        dref.users.set(users)

        # lets also add to operational update as well
        op_updates: models.QuerySet[DrefOperationalUpdate] = DrefOperationalUpdate.objects.filter(dref=dref.id)
        if op_updates.exists():
            for op in op_updates:
                op.users.set(users)

        # lets also add to the dref_final_report as well
        final_report: models.QuerySet[DrefFinalReport] = DrefFinalReport.objects.filter(dref=dref.id)
        if final_report.exists():
            final_report.first().users.set(users)

        # Send notification to newly added users
        if unique_emails:
            transaction.on_commit(
                lambda: send_dref_email.delay(
                    dref.id,
                    list(unique_emails),
                )
            )


class DrefShareUserSerializer(serializers.ModelSerializer):

    users_details = UserNameSerializer(source="users", many=True, read_only=True)

    class Meta:
        model = Dref
        fields = ("id", "users", "users_details")


class DrefGlobalFilesSerializer(serializers.Serializer):
    budget_template_url = serializers.CharField(read_only=True)


class BaseDref3Serializer(serializers.ModelSerializer):
    # Ephemeral numeric id (assigned per request in list view)
    id = serializers.IntegerField(read_only=True)
    appeal_id = serializers.CharField(source="appeal_code", read_only=True)
    stage = serializers.SerializerMethodField()
    allocation = serializers.SerializerMethodField()
    pillar = serializers.SerializerMethodField()
    appeal_type = serializers.SerializerMethodField()
    allocation_type = serializers.SerializerMethodField()
    country = serializers.CharField(source="country.name_en", read_only=True)
    country_iso3 = serializers.CharField(source="country.iso3", read_only=True)
    districts = serializers.SerializerMethodField()
    district_codes = serializers.SerializerMethodField()
    region = serializers.CharField(source="country.region", read_only=True)
    disaster_definition = serializers.CharField(source="disaster_type", read_only=True)
    disaster_name = serializers.CharField(source="title", read_only=True)
    type_of_onset = serializers.SerializerMethodField()
    crisis_categorization = serializers.SerializerMethodField()
    amount_approved = serializers.SerializerMethodField()
    total_approved = serializers.SerializerMethodField()
    date_of_disaster = serializers.CharField(source="event_date", read_only=True)
    date_of_appeal_request_from_ns = serializers.SerializerMethodField()
    date_of_approval = serializers.SerializerMethodField()
    date_of_summary_publication = serializers.SerializerMethodField()
    start_date_of_operation = serializers.SerializerMethodField()
    end_date_of_operation = serializers.SerializerMethodField()
    operation_status = serializers.SerializerMethodField()
    operation_timeframe = serializers.SerializerMethodField()
    modified_at = serializers.CharField(read_only=True)
    data_origin = serializers.SerializerMethodField()
    people_affected = serializers.SerializerMethodField()
    people_targeted = serializers.SerializerMethodField()
    people_assisted = serializers.SerializerMethodField()
    population_disaggregation = serializers.SerializerMethodField()
    sector_shelter_and_basic_household_items = serializers.SerializerMethodField()
    sector_shelter_and_basic_household_items_budget = serializers.SerializerMethodField()
    sector_shelter_and_basic_household_items_people_targeted = serializers.SerializerMethodField()
    sector_livelihoods = serializers.SerializerMethodField()
    sector_livelihoods_budget = serializers.SerializerMethodField()
    sector_livelihoods_people_targeted = serializers.SerializerMethodField()
    sector_multi_purpose_cash_grants = serializers.SerializerMethodField()
    sector_multi_purpose_cash_grants_budget = serializers.SerializerMethodField()
    sector_multi_purpose_cash_grants_people_targeted = serializers.SerializerMethodField()
    sector_health = serializers.SerializerMethodField()
    sector_health_budget = serializers.SerializerMethodField()
    sector_health_people_targeted = serializers.SerializerMethodField()
    sector_water_sanitation_and_hygiene = serializers.SerializerMethodField()
    sector_water_sanitation_and_hygiene_budget = serializers.SerializerMethodField()
    sector_water_sanitation_and_hygiene_people_targeted = serializers.SerializerMethodField()
    sector_protection_gender_and_inclusion = serializers.SerializerMethodField()
    sector_protection_gender_and_inclusion_budget = serializers.SerializerMethodField()
    sector_protection_gender_and_inclusion_people_targeted = serializers.SerializerMethodField()
    sector_education = serializers.SerializerMethodField()
    sector_education_budget = serializers.SerializerMethodField()
    sector_education_people_targeted = serializers.SerializerMethodField()
    sector_migration_and_displacement = serializers.SerializerMethodField()
    sector_migration_and_displacement_budget = serializers.SerializerMethodField()
    sector_migration_and_displacement_people_targeted = serializers.SerializerMethodField()
    sector_risk_reduction_climate_adaptation_and_recovery = serializers.SerializerMethodField()
    sector_risk_reduction_climate_adaptation_and_recovery_budget = serializers.SerializerMethodField()
    sector_risk_reduction_climate_adaptation_and_recovery_people_targeted = serializers.SerializerMethodField()
    sector_community_engagement_and_accountability = serializers.SerializerMethodField()
    sector_community_engagement_and_accountability_budget = serializers.SerializerMethodField()
    sector_community_engagement_and_accountability_people_targeted = serializers.SerializerMethodField()
    sector_environmental_sustainability = serializers.SerializerMethodField()
    sector_environmental_sustainability_budget = serializers.SerializerMethodField()
    sector_environmental_sustainability_people_targeted = serializers.SerializerMethodField()
    sector_coordination_and_partnerships = serializers.SerializerMethodField()
    sector_coordination_and_partnerships_budget = serializers.SerializerMethodField()
    sector_coordination_and_partnerships_people_targeted = serializers.SerializerMethodField()
    sector_secretariat_services = serializers.SerializerMethodField()
    sector_secretariat_services_budget = serializers.SerializerMethodField()
    sector_secretariat_services_people_targeted = serializers.SerializerMethodField()
    sector_national_society_strengthening = serializers.SerializerMethodField()
    sector_national_society_strengthening_budget = serializers.SerializerMethodField()
    sector_national_society_strengthening_people_targeted = serializers.SerializerMethodField()
    public = serializers.SerializerMethodField(read_only=True)
    is_latest_stage = serializers.SerializerMethodField(read_only=True)
    status = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    approved = serializers.SerializerMethodField()
    indicators_id = serializers.SerializerMethodField()
    link_to_emergency_page = serializers.SerializerMethodField()

    # get_id removed: numeric ids are injected post-serialization

    def get_public(self, obj):
        return self.context.get("public")

    def get_is_latest_stage(self, obj):
        return self.context.get("is_latest_stage")

    def get_stage(self, obj):
        return self.context.get("stage")

    def get_allocation(self, obj):
        return self.context.get("allocation")

    def get_pillar(self, obj):
        return "Anticipatory" if obj.type_of_dref == Dref.DrefType.IMMINENT else "Response"

    def get_appeal_type(self, obj):
        if obj.type_of_dref == Dref.DrefType.IMMINENT:
            return "i-DREF"
        elif obj.type_of_dref == Dref.DrefType.LOAN:
            return "EA"
        return "DREF"

    def get_allocation_type(self, obj):
        return "Loan" if obj.type_of_dref == Dref.DrefType.LOAN else "Grant"

    def get_districts(self, obj):
        return ", ".join(d.name for d in obj.district.all())

    def get_district_codes(self, obj):
        return ", ".join(d.code for d in obj.district.all())

    def get_type_of_onset(self, obj):
        type_of_onset = obj.type_of_onset if obj.type_of_onset != 0 else 1  # Default to "Slow Onset" if not set
        return Dref.OnsetType(type_of_onset).label

    def get_crisis_categorization(self, obj):
        if hasattr(obj, "disaster_category") and obj.disaster_category is not None:
            return Dref.DisasterCategory(obj.disaster_category).label
        return "Yellow (?)"

    def get_amount_approved(self, obj):
        if hasattr(obj, "amount_requested"):
            return obj.amount_requested
        if hasattr(obj, "additional_allocation"):
            return obj.additional_allocation
        return 0

    def get_total_approved(self, obj):
        if hasattr(obj, "total_dref_allocation"):
            return obj.total_dref_allocation
        if hasattr(obj, "amount_requested"):
            return obj.amount_requested
        return 0

    def get_date_of_appeal_request_from_ns(self, obj):
        if type(obj).__name__ == "Dref" and hasattr(obj, "ns_request_date"):
            return obj.ns_request_date

    def get_date_of_approval(self, obj):
        # if type(obj).__name__ == "Dref" and hasattr(obj, "date_of_approval"): – instead of this, just return for all types
        if hasattr(obj, "date_of_approval"):
            return obj.date_of_approval

    def get_date_of_summary_publication(self, obj):
        if type(obj).__name__ == "Dref" and hasattr(obj, "publishing_date"):
            return obj.publishing_date

    def get_start_date_of_operation(self, obj):
        if hasattr(obj, "event_date"):
            return obj.event_date

    def get_end_date_of_operation(self, obj):
        t = type(obj).__name__
        if t == "Dref" and hasattr(obj, "end_date"):
            return obj.end_date
        if t == "DrefOperationalUpdate" and hasattr(obj, "new_operational_end_date"):
            return obj.new_operational_end_date
        if t == "DrefFinalReport" and hasattr(obj, "operation_end_date"):
            return obj.operation_end_date

    def get_operation_status(self, obj):
        """Return 'active' if current date is between start and end date (inclusive), else 'closed'.
        Returns None if either boundary date is missing.
        """
        start = self.get_start_date_of_operation(obj)
        end = self.get_end_date_of_operation(obj)
        if not start or not end:
            return None
        try:
            today = timezone.now().date()
            # Ensure we are comparing date objects (convert datetimes if present)
            if hasattr(start, "date") and callable(getattr(start, "date")):
                start = start.date()
            if hasattr(end, "date") and callable(getattr(end, "date")):
                end = end.date()
            return "active" if start <= today <= end else "closed"
        except Exception:
            return None

    def get_operation_timeframe(self, obj):
        t = type(obj).__name__
        if t == "Dref" and hasattr(obj, "operation_timeframe"):
            return obj.operation_timeframe
        if t != "Dref" and hasattr(obj, "total_operation_timeframe"):  # OU + FR:
            return obj.total_operation_timeframe

    def get_data_origin(self, obj):
        return "DREF process in GO"  # Hardcoded for now, later can be also "DREF published report"

    def get_people_affected(self, obj):
        t = type(obj).__name__
        if t == "Dref" and hasattr(obj, "num_affected"):
            return obj.num_affected
        if t != "Dref" and hasattr(obj, "number_of_people_affected"):  # OU + FR:
            return obj.number_of_people_affected

    def get_people_targeted(self, obj):
        t = type(obj).__name__
        if t != "DrefOperationalUpdate" and hasattr(obj, "total_targeted_population"):  # A + FR:
            return obj.total_targeted_population
        if t == "DrefOperationalUpdate" and hasattr(obj, "number_of_people_targeted"):
            return obj.number_of_people_targeted

    def get_people_assisted(self, obj):
        if type(obj).__name__ == "DrefFinalReport":
            return obj.num_assisted

    def get_population_disaggregation(self, obj):
        """Return population disaggregation dict.

        Structure:
        {
            "Women": women,
            "Girls (under 18)": girls,
            "Men": men,
            "Boys (under 18)": boys,
            "Rural": "people_per_local%",
            "Urban": "people_per_urban%"
        }
        Only include keys that have a non-None underlying value.
        Percentages are suffixed with % if numeric.
        """
        women = getattr(obj, "women", None)
        girls = getattr(obj, "girls", None)
        men = getattr(obj, "men", None)
        boys = getattr(obj, "boys", None)
        urban = getattr(obj, "people_per_urban", None)
        rural = getattr(obj, "people_per_local", None)

        def pct(val):
            if val is None:
                return None
            try:
                # Keep as int if float-ish, then append %
                return f"{int(val)}%"
            except (ValueError, TypeError):
                return None

        data = {}
        if women is not None:
            data["Women"] = women
        if girls is not None:
            data["Girls (under 18)"] = girls
        if men is not None:
            data["Men"] = men
        if boys is not None:
            data["Boys (under 18)"] = boys
        if rural is not None:
            rural_pct = pct(rural)
            if rural_pct is not None:
                data["Rural"] = rural_pct
        if urban is not None:
            urban_pct = pct(urban)
            if urban_pct is not None:
                data["Urban"] = urban_pct

        return data or None

    def get_sector_shelter_and_basic_household_items(self, obj):
        topic = PlannedIntervention.Title.SHELTER_HOUSING_AND_SETTLEMENTS
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_shelter_and_basic_household_items_budget(self, obj):
        topic = PlannedIntervention.Title.SHELTER_HOUSING_AND_SETTLEMENTS
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_shelter_and_basic_household_items_people_targeted(self, obj):
        topic = PlannedIntervention.Title.SHELTER_HOUSING_AND_SETTLEMENTS
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_livelihoods(self, obj):
        topic = PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_livelihoods_budget(self, obj):
        topic = PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_livelihoods_people_targeted(self, obj):
        topic = PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_multi_purpose_cash_grants(self, obj):
        topic = PlannedIntervention.Title.MULTI_PURPOSE_CASH
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_multi_purpose_cash_grants_budget(self, obj):
        topic = PlannedIntervention.Title.MULTI_PURPOSE_CASH
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_multi_purpose_cash_grants_people_targeted(self, obj):
        topic = PlannedIntervention.Title.MULTI_PURPOSE_CASH
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_health(self, obj):
        topic = PlannedIntervention.Title.HEALTH
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_health_budget(self, obj):
        topic = PlannedIntervention.Title.HEALTH
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_health_people_targeted(self, obj):
        topic = PlannedIntervention.Title.HEALTH
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_water_sanitation_and_hygiene(self, obj):
        topic = PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_water_sanitation_and_hygiene_budget(self, obj):
        topic = PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_water_sanitation_and_hygiene_people_targeted(self, obj):
        topic = PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_protection_gender_and_inclusion(self, obj):
        topic = PlannedIntervention.Title.PROTECTION_GENDER_AND_INCLUSION
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_protection_gender_and_inclusion_budget(self, obj):
        topic = PlannedIntervention.Title.PROTECTION_GENDER_AND_INCLUSION
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_protection_gender_and_inclusion_people_targeted(self, obj):
        topic = PlannedIntervention.Title.PROTECTION_GENDER_AND_INCLUSION
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_education(self, obj):
        topic = PlannedIntervention.Title.EDUCATION
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_education_budget(self, obj):
        topic = PlannedIntervention.Title.EDUCATION
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_education_people_targeted(self, obj):
        topic = PlannedIntervention.Title.EDUCATION
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_migration_and_displacement(self, obj):
        topic = PlannedIntervention.Title.MIGRATION_AND_DISPLACEMENT
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_migration_and_displacement_budget(self, obj):
        topic = PlannedIntervention.Title.MIGRATION_AND_DISPLACEMENT
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_migration_and_displacement_people_targeted(self, obj):
        topic = PlannedIntervention.Title.MIGRATION_AND_DISPLACEMENT
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_risk_reduction_climate_adaptation_and_recovery(self, obj):
        topic = PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_risk_reduction_climate_adaptation_and_recovery_budget(self, obj):
        topic = PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_risk_reduction_climate_adaptation_and_recovery_people_targeted(self, obj):
        topic = PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_community_engagement_and_accountability(self, obj):
        topic = PlannedIntervention.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_community_engagement_and_accountability_budget(self, obj):
        topic = PlannedIntervention.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_community_engagement_and_accountability_people_targeted(self, obj):
        topic = PlannedIntervention.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_environmental_sustainability(self, obj):
        topic = PlannedIntervention.Title.ENVIRONMENTAL_SUSTAINABILITY
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_environmental_sustainability_budget(self, obj):
        topic = PlannedIntervention.Title.ENVIRONMENTAL_SUSTAINABILITY
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_environmental_sustainability_people_targeted(self, obj):
        topic = PlannedIntervention.Title.ENVIRONMENTAL_SUSTAINABILITY
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_coordination_and_partnerships(self, obj):
        topic = PlannedIntervention.Title.COORDINATION_AND_PARTNERSHIPS
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_coordination_and_partnerships_budget(self, obj):
        topic = PlannedIntervention.Title.COORDINATION_AND_PARTNERSHIPS
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_coordination_and_partnerships_people_targeted(self, obj):
        topic = PlannedIntervention.Title.COORDINATION_AND_PARTNERSHIPS
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_secretariat_services(self, obj):
        topic = PlannedIntervention.Title.SECRETARIAT_SERVICES
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_secretariat_services_budget(self, obj):
        topic = PlannedIntervention.Title.SECRETARIAT_SERVICES
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_secretariat_services_people_targeted(self, obj):
        topic = PlannedIntervention.Title.SECRETARIAT_SERVICES
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_national_society_strengthening(self, obj):
        topic = PlannedIntervention.Title.NATIONAL_SOCIETY_STRENGTHENING
        return True if any(p.title == topic for p in obj.planned_interventions.all()) else False

    def get_sector_national_society_strengthening_budget(self, obj):
        topic = PlannedIntervention.Title.NATIONAL_SOCIETY_STRENGTHENING
        if obj.planned_interventions.count():
            return sum([(p.budget or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_sector_national_society_strengthening_people_targeted(self, obj):
        topic = PlannedIntervention.Title.NATIONAL_SOCIETY_STRENGTHENING
        if obj.planned_interventions.count():
            return sum([(p.person_targeted or 0) for p in obj.planned_interventions.all() if p.title == topic])

    def get_approved(self, obj):
        return True if obj.status == Dref.Status.APPROVED else False

    def get_indicators_id(self, obj):
        return None  # Placeholder for future implementation

    def get_link_to_emergency_page(self, obj):
        try:
            appeal = Appeal.objects.get(code=obj.appeal_code)
        except Appeal.DoesNotExist:
            return None  # f"No Appeal (and no Event) found with code: {obj.appeal_code}"
        return f"https://go.ifrc.org/emergencies/{appeal.event_id}/details"

    class Meta:
        abstract = True
        fields = [
            "id",
            "appeal_id",
            "stage",
            "allocation",
            "pillar",
            "appeal_type",
            "allocation_type",
            "country",
            "country_iso3",
            "districts",
            "district_codes",
            "region",
            "disaster_definition",
            "disaster_name",
            "type_of_onset",
            "crisis_categorization",
            "amount_approved",
            "total_approved",
            "date_of_disaster",
            "date_of_appeal_request_from_ns",
            "date_of_approval",
            "date_of_summary_publication",
            "start_date_of_operation",
            "end_date_of_operation",
            "operation_status",
            "operation_timeframe",
            "modified_at",
            "data_origin",
            "people_affected",
            "people_targeted",
            "people_assisted",
            "population_disaggregation",
            "sector_shelter_and_basic_household_items",
            "sector_shelter_and_basic_household_items_budget",
            "sector_shelter_and_basic_household_items_people_targeted",
            "sector_livelihoods",
            "sector_livelihoods_budget",
            "sector_livelihoods_people_targeted",
            "sector_multi_purpose_cash_grants",
            "sector_multi_purpose_cash_grants_budget",
            "sector_multi_purpose_cash_grants_people_targeted",
            "sector_health",
            "sector_health_budget",
            "sector_health_people_targeted",
            "sector_water_sanitation_and_hygiene",
            "sector_water_sanitation_and_hygiene_budget",
            "sector_water_sanitation_and_hygiene_people_targeted",
            "sector_protection_gender_and_inclusion",
            "sector_protection_gender_and_inclusion_budget",
            "sector_protection_gender_and_inclusion_people_targeted",
            "sector_education",
            "sector_education_budget",
            "sector_education_people_targeted",
            "sector_migration_and_displacement",
            "sector_migration_and_displacement_budget",
            "sector_migration_and_displacement_people_targeted",
            "sector_risk_reduction_climate_adaptation_and_recovery",
            "sector_risk_reduction_climate_adaptation_and_recovery_budget",
            "sector_risk_reduction_climate_adaptation_and_recovery_people_targeted",
            "sector_community_engagement_and_accountability",
            "sector_community_engagement_and_accountability_budget",
            "sector_community_engagement_and_accountability_people_targeted",
            "sector_environmental_sustainability",
            "sector_environmental_sustainability_budget",
            "sector_environmental_sustainability_people_targeted",
            "sector_coordination_and_partnerships",
            "sector_coordination_and_partnerships_budget",
            "sector_coordination_and_partnerships_people_targeted",
            "sector_secretariat_services",
            "sector_secretariat_services_budget",
            "sector_secretariat_services_people_targeted",
            "sector_national_society_strengthening",
            "sector_national_society_strengthening_budget",
            "sector_national_society_strengthening_people_targeted",
            "public",
            "is_latest_stage",
            "status",
            "status_display",
            "approved",
            "indicators_id",
            "link_to_emergency_page",
        ]


class Dref3Serializer(BaseDref3Serializer):
    class Meta(BaseDref3Serializer.Meta):
        model = Dref


class DrefOperationalUpdate3Serializer(BaseDref3Serializer):
    class Meta(BaseDref3Serializer.Meta):
        model = DrefOperationalUpdate


class DrefFinalReport3Serializer(BaseDref3Serializer):
    class Meta(BaseDref3Serializer.Meta):
        model = DrefFinalReport
