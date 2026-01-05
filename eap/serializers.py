import typing

from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from api.serializers import (
    Admin2Serializer,
    DisasterTypeSerializer,
    MiniCountrySerializer,
    UserNameSerializer,
)
from eap.models import (
    DaysTimeFrameChoices,
    EAPAction,
    EAPContact,
    EAPFile,
    EAPImpact,
    EAPRegistration,
    EAPType,
    EnableApproach,
    FullEAP,
    HoursTimeFrameChoices,
    Indicator,
    KeyActor,
    MonthsTimeFrameChoices,
    OperationActivity,
    PlannedOperation,
    SimplifiedEAP,
    SourceInformation,
    TimeFrame,
    YearsTimeFrameChoices,
)
from eap.tasks import generate_eap_summary_pdf, generate_export_diff_pdf
from eap.utils import (
    has_country_permission,
    is_user_ifrc_admin,
    validate_file_extention,
)
from main.writable_nested_serializers import NestedCreateMixin, NestedUpdateMixin
from utils.file_check import validate_file_type

ALLOWED_FILE_EXTENTIONS: list[str] = ["pdf", "docx", "pptx", "xlsx", "xlsm"]


class BaseEAPSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        # NOTE: Setting `created_by` and `modified_by` required to False
        fields["created_by"] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            required=False,
        )
        fields["modified_by"] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            required=False,
        )

        fields["created_by_details"] = UserNameSerializer(source="created_by", read_only=True)
        fields["modified_by_details"] = UserNameSerializer(source="modified_by", read_only=True)
        return fields

    def _set_user_fields(self, validated_data: dict[str, typing.Any], fields: list[str]) -> None:
        """Set user fields if they exist in the model."""
        model_fields = self.Meta.model._meta._forward_fields_map
        user = self.context["request"].user

        for field in fields:
            if field in model_fields:
                validated_data[field] = user

    def create(self, validated_data: dict[str, typing.Any]):
        self._set_user_fields(validated_data, ["created_by", "modified_by"])
        return super().create(validated_data)

    def update(self, instance, validated_data: dict[str, typing.Any]):
        self._set_user_fields(validated_data, ["modified_by"])
        return super().update(instance, validated_data)


# NOTE: Mini Serializers used for basic listing purpose


class MiniSimplifiedEAPSerializer(
    serializers.ModelSerializer,
):
    class Meta:
        model = SimplifiedEAP
        fields = [
            "id",
            "eap_registration",
            "total_budget",
            "readiness_budget",
            "pre_positioning_budget",
            "early_action_budget",
            "seap_timeframe",
            "budget_file",
            "version",
            "is_locked",
            "updated_checklist_file",
            "created_at",
            "modified_at",
        ]


class MiniFullEAPSerializer(
    serializers.ModelSerializer,
):
    class Meta:
        model = FullEAP
        fields = [
            "id",
            "eap_registration",
            "total_budget",
            "readiness_budget",
            "pre_positioning_budget",
            "early_action_budget",
            "budget_file",
            "version",
            "is_locked",
            "updated_checklist_file",
            "created_at",
            "modified_at",
        ]


class MiniEAPSerializer(serializers.ModelSerializer):
    eap_type_display = serializers.CharField(source="get_eap_type_display", read_only=True)
    country_details = MiniCountrySerializer(source="country", read_only=True)
    disaster_type_details = DisasterTypeSerializer(source="disaster_type", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    requirement_cost = serializers.IntegerField(read_only=True)

    class Meta:
        model = EAPRegistration
        fields = [
            "id",
            "country",
            "country_details",
            "eap_type",
            "eap_type_display",
            "disaster_type",
            "disaster_type_details",
            "status",
            "status_display",
            "requirement_cost",
            "activated_at",
            "approved_at",
            "created_at",
            "modified_at",
        ]


class EAPRegistrationSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    BaseEAPSerializer,
):
    country_details = MiniCountrySerializer(source="country", read_only=True)
    national_society_details = MiniCountrySerializer(source="national_society", read_only=True)
    partners_details = MiniCountrySerializer(source="partners", many=True, read_only=True)

    eap_type_display = serializers.CharField(source="get_eap_type_display", read_only=True)
    disaster_type_details = DisasterTypeSerializer(source="disaster_type", read_only=True)

    # EAPs
    simplified_eap_details = MiniSimplifiedEAPSerializer(source="simplified_eap", many=True, read_only=True)
    full_eap_details = MiniFullEAPSerializer(source="full_eap", many=True, read_only=True)

    # Status
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EAPRegistration
        fields = "__all__"
        read_only_fields = [
            "status",
            "validated_budget_file",
            "modified_at",
            "created_by",
            "modified_by",
            "latest_simplified_eap",
            "latest_full_eap",
        ]

    def update(self, instance: EAPRegistration, validated_data: dict[str, typing.Any]) -> dict[str, typing.Any]:
        # NOTE: Cannot update once EAP application is being created.
        if instance.has_eap_application:
            raise serializers.ValidationError("Cannot update EAP Registration once application is being created.")
        return super().update(instance, validated_data)


class EAPValidatedBudgetFileSerializer(serializers.ModelSerializer):
    validated_budget_file = serializers.FileField(required=True)

    class Meta:
        model = EAPRegistration
        fields = [
            "id",
            "validated_budget_file",
        ]

    def validate(self, validated_data: dict[str, typing.Any]) -> dict[str, typing.Any]:
        assert self.instance is not None, "EAP instance does not exist."
        if self.instance.get_status_enum != EAPRegistration.Status.TECHNICALLY_VALIDATED:
            raise serializers.ValidationError(
                gettext("Validated budget file can only be uploaded when EAP status is %s."),
                EAPRegistration.Status.TECHNICALLY_VALIDATED.label,
            )

        validate_file_type(validated_data["validated_budget_file"])
        validate_file_extention(validated_data["validated_budget_file"].name, ALLOWED_FILE_EXTENTIONS)
        return validated_data


class EAPFileInputSerializer(serializers.Serializer):
    file = serializers.ListField(child=serializers.FileField(required=True))


class EAPGlobalFilesSerializer(serializers.Serializer):
    url = serializers.URLField(read_only=True)


class EAPFileSerializer(BaseEAPSerializer):
    id = serializers.IntegerField(required=False)
    file = serializers.FileField(required=True)

    class Meta:
        model = EAPFile
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "modified_by",
        )

    def validate_file(self, file):
        validate_file_type(file)
        return file


# NOTE: Separate serializer for partial updating EAPFile instance
class EAPFileUpdateSerializer(BaseEAPSerializer):
    id = serializers.IntegerField(required=True)
    file = serializers.FileField(required=False)

    class Meta:
        model = EAPFile
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "modified_by",
        )

    def validate_id(self, id: int) -> int:
        try:
            EAPFile.objects.get(id=id)
        except EAPFile.DoesNotExist:
            raise serializers.ValidationError(gettext("Invalid pk '%s' - object does not exist.") % id)
        return id

    def validate_file(self, file):
        validate_file_type(file)
        return file


ALLOWED_MAP_TIMEFRAMES_VALUE = {
    TimeFrame.YEARS: list(YearsTimeFrameChoices.values),
    TimeFrame.MONTHS: list(MonthsTimeFrameChoices.values),
    TimeFrame.DAYS: list(DaysTimeFrameChoices.values),
    TimeFrame.HOURS: list(HoursTimeFrameChoices.values),
}


class OperationActivitySerializer(
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    timeframe = serializers.ChoiceField(
        choices=TimeFrame.choices,
        required=True,
    )
    timeframe_display = serializers.CharField(source="get_timeframe_display", read_only=True)
    time_value = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
    )

    class Meta:
        model = OperationActivity
        fields = "__all__"

    # NOTE: Custom validation for `timeframe` and `time_value`
    # Make sure time_value is within the allowed range for the selected timeframe
    def validate(self, validated_data: dict[str, typing.Any]) -> dict[str, typing.Any]:
        timeframe = validated_data["timeframe"]
        time_value = validated_data["time_value"]

        allowed_values = ALLOWED_MAP_TIMEFRAMES_VALUE.get(timeframe, [])
        invalid_values = [value for value in time_value if value not in allowed_values]

        if invalid_values:
            raise serializers.ValidationError(
                {
                    "time_value": gettext("Invalid time_value(s) %s for the selected timeframe %s.")
                    % (invalid_values, TimeFrame(timeframe).label)
                }
            )
        return validated_data


class IndicatorSerializer(
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Indicator
        fields = "__all__"


class PlannedOperationSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)

    indicators = IndicatorSerializer(many=True, required=True)

    # activities
    readiness_activities = OperationActivitySerializer(many=True, required=True)
    prepositioning_activities = OperationActivitySerializer(many=True, required=True)
    early_action_activities = OperationActivitySerializer(many=True, required=True)

    class Meta:
        model = PlannedOperation
        fields = "__all__"


class EnableApproachSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)

    indicators = IndicatorSerializer(many=True, required=True)

    # activities
    readiness_activities = OperationActivitySerializer(many=True, required=True)
    prepositioning_activities = OperationActivitySerializer(many=True, required=True)
    early_action_activities = OperationActivitySerializer(many=True, required=True)

    class Meta:
        model = EnableApproach
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "modified_by",
        )


class EAPSourceInformationSerializer(
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = SourceInformation
        fields = "__all__"


class KeyActorSerializer(
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    national_society_details = MiniCountrySerializer(source="national_society", read_only=True)

    class Meta:
        model = KeyActor
        fields = "__all__"


class EAPActionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = EAPAction
        fields = "__all__"


class ImpactSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = EAPImpact
        fields = "__all__"




class EAPContactSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = EAPContact
        fields = (
            "id",
            "title",
            "name",
            "email",
            "phone_number",
        )


class CommonEAPFieldsSerializer(serializers.ModelSerializer):
    MAX_NUMBER_OF_IMAGES = 5

    # Partner NS Contact
    partner_contacts = EAPContactSerializer(many=True, required=False)

    planned_operations = PlannedOperationSerializer(many=True, required=False)
    enable_approaches = EnableApproachSerializer(many=True, required=False)

    # FILES
    cover_image_file = EAPFileUpdateSerializer(source="cover_image", required=False, allow_null=True)
    admin2_details = Admin2Serializer(source="admin2", many=True, read_only=True)
    budget_file_details = EAPFileSerializer(source="budget_file", read_only=True)

    def get_fields(self):
        fields = super().get_fields()
        fields["partner_contacts"] = EAPContactSerializer(many=True, required=False)
        # TODO(susilnem): Make admin2 required once we verify the data!
        fields["admin2_details"] = Admin2Serializer(source="admin2", many=True, read_only=True)
        fields["cover_image_file"] = EAPFileUpdateSerializer(source="cover_image", required=False, allow_null=True)
        fields["planned_operations"] = PlannedOperationSerializer(many=True, required=False)
        fields["enable_approaches"] = EnableApproachSerializer(many=True, required=False)
        fields["budget_file_details"] = EAPFileSerializer(source="budget_file", read_only=True)
        return fields

    def validate_budget_file(self, file: typing.Optional[EAPFile]) -> typing.Optional[EAPFile]:
        if file is None:
            return

        validate_file_extention(file.file.name, ALLOWED_FILE_EXTENTIONS)
        return file

    def validate_updated_checklist_file(self, file):
        if file is None:
            return

        validate_file_extention(file.file.name, ALLOWED_FILE_EXTENTIONS)
        validate_file_type(file.file)
        return file

    def validate_images_field(self, field_name, images):
        if images and len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(
                {field_name: [f"Maximum {self.MAX_NUMBER_OF_IMAGES} images are allowed."]},
            )
        return images


class SimplifiedEAPSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    BaseEAPSerializer,
    CommonEAPFieldsSerializer,
):

    # FILES
    hazard_impact_images = EAPFileUpdateSerializer(required=False, many=True)
    selected_early_actions_images = EAPFileUpdateSerializer(required=False, many=True, allow_null=True)
    risk_selected_protocols_images = EAPFileUpdateSerializer(required=False, many=True, allow_null=True)

    # TimeFrame
    seap_lead_timeframe_unit_display = serializers.CharField(source="get_seap_lead_timeframe_unit_display", read_only=True)
    operational_timeframe_unit_display = serializers.CharField(source="get_operational_timeframe_unit_display", read_only=True)

    # IMAGES

    # NOTE: When adding new image fields, include their names in IMAGE_FIELDS below
    # if the image fields are to be validated against the MAX_NUMBER_OF_IMAGES limit.

    IMAGE_FIELDS = [
        "hazard_impact_images",
        "selected_early_actions_images",
        "risk_selected_protocols_images",
    ]

    class Meta:
        model = SimplifiedEAP
        read_only_fields = [
            "version",
            "is_locked",
        ]
        exclude = ("cover_image",)

    def _validate_timeframe(self, data: dict[str, typing.Any]) -> None:
        # --- seap lead TimeFrame ---
        seap_unit = data.get("seap_lead_timeframe_unit")
        seap_value = data.get("seap_lead_time")

        if (seap_unit is None) != (seap_value is None):
            raise serializers.ValidationError(
                {"seap_lead_timeframe_unit": gettext("seap lead timeframe and unit must both be provided.")}
            )

        if seap_unit is not None and seap_value is not None:
            allowed_units = [
                TimeFrame.MONTHS,
                TimeFrame.DAYS,
                TimeFrame.HOURS,
            ]
            if seap_unit not in allowed_units:
                raise serializers.ValidationError(
                    {
                        "seap_lead_timeframe_unit": gettext(
                            "seap lead timeframe unit must be one of the following: Months, Days, or Hours."
                        )
                    }
                )

        # --- Operational TimeFrame ---
        op_unit = data.get("operational_timeframe_unit")
        op_value = data.get("operational_timeframe")

        # Require both if one is provided
        if (op_unit is None) != (op_value is None):
            raise serializers.ValidationError(
                {"operational_timeframe_unit": gettext("operational timeframe and unit must both be provided.")}
            )

        if op_unit is not None and op_value is not None:
            if op_unit != TimeFrame.MONTHS:
                raise serializers.ValidationError(
                    {"operational_timeframe_unit": gettext("operational timeframe unit must be Months.")}
                )

            if op_value not in MonthsTimeFrameChoices:
                raise serializers.ValidationError(
                    {"operational_timeframe": gettext("operational timeframe value is not valid for Months unit.")}
                )

    def validate(self, data: dict[str, typing.Any]) -> dict[str, typing.Any]:
        original_eap_registration = getattr(self.instance, "eap_registration", None) if self.instance else None
        eap_registration: EAPRegistration | None = data.get("eap_registration", original_eap_registration)
        assert eap_registration is not None, "EAP Registration must be provided."

        if self.instance and original_eap_registration != eap_registration:
            raise serializers.ValidationError("EAP Registration cannot be changed for existing EAP.")

        if not self.instance and eap_registration.has_eap_application:
            raise serializers.ValidationError("Simplified EAP for this EAP registration already exists.")

        if self.instance and eap_registration.get_status_enum not in [
            EAPRegistration.Status.UNDER_DEVELOPMENT,
            EAPRegistration.Status.NS_ADDRESSING_COMMENTS,
        ]:
            raise serializers.ValidationError(
                gettext("Cannot update while EAP Application is in %s."),
                EAPRegistration.Status(eap_registration.get_status_enum).label,
            )

        # NOTE: Cannot update locked Simplified EAP
        if self.instance and self.instance.is_locked:
            raise serializers.ValidationError("Cannot update locked EAP Application.")

        eap_type = eap_registration.get_eap_type_enum
        if eap_type and eap_type != EAPType.SIMPLIFIED_EAP:
            raise serializers.ValidationError("Cannot create Simplified EAP for non-simplified EAP registration.")

        # Validate timeframe fields
        self._validate_timeframe(data)

        # Validate all image fields in one place
        for field in self.IMAGE_FIELDS:
            if field in data:
                self.validate_images_field(field, data[field])
        return data

    def create(self, validated_data: dict[str, typing.Any]):
        instance: SimplifiedEAP = super().create(validated_data)
        instance.eap_registration.update_eap_type(EAPType.SIMPLIFIED_EAP)
        instance.eap_registration.latest_simplified_eap = instance
        instance.eap_registration.save(update_fields=["latest_simplified_eap"])
        return instance


class FullEAPSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    BaseEAPSerializer,
    CommonEAPFieldsSerializer,
):

    # admins
    key_actors = KeyActorSerializer(many=True, required=True)

    early_actions = EAPActionSerializer(many=True, required=False)
    prioritized_impacts = ImpactSerializer(many=True, required=False)

    # SOURCE OF INFORMATIONS
    risk_analysis_source_of_information = EAPSourceInformationSerializer(many=True, required=False, allow_null=True)
    trigger_statement_source_of_information = EAPSourceInformationSerializer(many=True, required=False, allow_null=True)
    trigger_model_source_of_information = EAPSourceInformationSerializer(many=True, required=False, allow_null=True)
    evidence_base_source_of_information = EAPSourceInformationSerializer(many=True, required=False, allow_null=True)
    activation_process_source_of_information = EAPSourceInformationSerializer(many=True, required=False, allow_null=True)

    # IMAGES
    hazard_selection_images = EAPFileUpdateSerializer(
        many=True,
        required=False,
        allow_null=True,
    )
    exposed_element_and_vulnerability_factor_images = EAPFileUpdateSerializer(
        many=True,
        required=False,
        allow_null=True,
    )
    prioritized_impact_images = EAPFileUpdateSerializer(
        many=True,
        required=False,
        allow_null=True,
    )
    forecast_selection_images = EAPFileUpdateSerializer(
        many=True,
        required=False,
        allow_null=True,
    )
    definition_and_justification_impact_level_images = EAPFileUpdateSerializer(
        many=True,
        required=False,
        allow_null=True,
    )
    identification_of_the_intervention_area_images = EAPFileUpdateSerializer(
        many=True,
        required=False,
        allow_null=True,
    )
    early_action_selection_process_images = EAPFileUpdateSerializer(
        many=True,
        required=False,
        allow_null=True,
    )
    early_action_implementation_images = EAPFileUpdateSerializer(
        many=True,
        required=False,
        allow_null=True,
    )
    trigger_activation_system_images = EAPFileUpdateSerializer(
        many=True,
        required=False,
        allow_null=True,
    )

    # FILES
    forecast_table_file_details = EAPFileSerializer(source="forecast_table_file", read_only=True)
    forecast_table_file = serializers.PrimaryKeyRelatedField(
        queryset=EAPFile.objects.all(),
        required=True,
        allow_null=False,
    )

    theory_of_change_table_file_details = EAPFileSerializer(source="theory_of_change_table_file", read_only=True)
    risk_analysis_relevant_files_details = EAPFileSerializer(source="risk_analysis_relevant_files", many=True, read_only=True)
    evidence_base_relevant_files_details = EAPFileSerializer(source="evidence_base_relevant_files", many=True, read_only=True)
    activation_process_relevant_files_details = EAPFileSerializer(
        source="activation_process_relevant_files", many=True, read_only=True
    )
    trigger_model_relevant_files_details = EAPFileSerializer(source="trigger_model_relevant_files", many=True, read_only=True)
    meal_relevant_files_details = EAPFileSerializer(source="meal_relevant_files", many=True, read_only=True)
    capacity_relevant_files_details = EAPFileSerializer(source="capacity_relevant_files", many=True, read_only=True)

    # NOTE: When adding new image fields, include their names in IMAGE_FIELDS below
    # if the image fields are to be validated against the MAX_NUMBER_OF_IMAGES limit.

    IMAGE_FIELDS = [
        "hazard_selection_images",
        "exposed_element_and_vulnerability_factor_images",
        "prioritized_impact_images",
        "forecast_selection_images",
        "definition_and_justification_impact_level_images",
        "identification_of_the_intervention_area_images",
        "early_action_selection_process_images",
        "early_action_implementation_images",
        "trigger_activation_system_images",
    ]

    class Meta:
        model = FullEAP
        read_only_fields = (
            "created_by",
            "modified_by",
        )
        exclude = ("cover_image",)

    def validate(self, data: dict[str, typing.Any]) -> dict[str, typing.Any]:
        original_eap_registration = getattr(self.instance, "eap_registration", None) if self.instance else None
        eap_registration: EAPRegistration | None = data.get("eap_registration", original_eap_registration)
        assert eap_registration is not None, "EAP Registration must be provided."

        if self.instance and original_eap_registration != eap_registration:
            raise serializers.ValidationError("EAP Registration cannot be changed for existing EAP.")

        if not self.instance and eap_registration.has_eap_application:
            raise serializers.ValidationError("Full EAP for this EAP registration already exists.")

        if self.instance and eap_registration.get_status_enum not in [
            EAPRegistration.Status.UNDER_DEVELOPMENT,
            EAPRegistration.Status.NS_ADDRESSING_COMMENTS,
        ]:
            raise serializers.ValidationError(
                gettext("Cannot update while EAP Application is in %s."),
                EAPRegistration.Status(eap_registration.get_status_enum).label,
            )

        # NOTE: Cannot update locked Full EAP
        if self.instance and self.instance.is_locked:
            raise serializers.ValidationError("Cannot update locked EAP Application.")

        eap_type = eap_registration.get_eap_type_enum
        if eap_type and eap_type != EAPType.FULL_EAP:
            raise serializers.ValidationError("Cannot create Full EAP for non-full EAP registration.")

        # Validate all image fields in one place
        for field in self.IMAGE_FIELDS:
            if field in data:
                self.validate_images_field(field, data[field])
        return data

    def create(self, validated_data: dict[str, typing.Any]):
        instance: FullEAP = super().create(validated_data)
        instance.eap_registration.update_eap_type(EAPType.FULL_EAP)
        instance.eap_registration.latest_full_eap = instance
        instance.eap_registration.save(update_fields=["latest_full_eap"])
        return instance


# STATUS TRANSITION SERIALIZER
VALID_NS_EAP_STATUS_TRANSITIONS = set(
    [
        (EAPRegistration.Status.UNDER_DEVELOPMENT, EAPRegistration.Status.UNDER_REVIEW),
        (EAPRegistration.Status.NS_ADDRESSING_COMMENTS, EAPRegistration.Status.UNDER_REVIEW),
    ]
)


VALID_IFRC_EAP_STATUS_TRANSITIONS = set(
    [
        (EAPRegistration.Status.UNDER_DEVELOPMENT, EAPRegistration.Status.UNDER_REVIEW),
        (EAPRegistration.Status.UNDER_REVIEW, EAPRegistration.Status.NS_ADDRESSING_COMMENTS),
        (EAPRegistration.Status.NS_ADDRESSING_COMMENTS, EAPRegistration.Status.UNDER_REVIEW),
        (EAPRegistration.Status.UNDER_REVIEW, EAPRegistration.Status.TECHNICALLY_VALIDATED),
        (EAPRegistration.Status.TECHNICALLY_VALIDATED, EAPRegistration.Status.NS_ADDRESSING_COMMENTS),
        (EAPRegistration.Status.TECHNICALLY_VALIDATED, EAPRegistration.Status.PENDING_PFA),
        (EAPRegistration.Status.PENDING_PFA, EAPRegistration.Status.APPROVED),
        (EAPRegistration.Status.APPROVED, EAPRegistration.Status.ACTIVATED),
    ]
)


class EAPStatusSerializer(BaseEAPSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    # NOTE: Only required when changing status to NS Addressing Comments
    review_checklist_file = serializers.FileField(required=False)

    class Meta:
        model = EAPRegistration
        fields = [
            "id",
            "status_display",
            "status",
            "review_checklist_file",
        ]

    def _validate_status(self, validated_data: dict[str, typing.Any]) -> dict[str, typing.Any]:
        assert self.instance is not None, "EAP instance does not exist."
        self.instance: EAPRegistration

        if not self.instance.has_eap_application:
            raise serializers.ValidationError(gettext("You cannot change the status until EAP application has been created."))

        user = self.context["request"].user
        current_status: EAPRegistration.Status = self.instance.get_status_enum
        new_status: EAPRegistration.Status = EAPRegistration.Status(validated_data.get("status"))

        valid_transitions = VALID_IFRC_EAP_STATUS_TRANSITIONS if is_user_ifrc_admin(user) else VALID_NS_EAP_STATUS_TRANSITIONS

        if (current_status, new_status) not in valid_transitions:
            raise serializers.ValidationError(
                gettext("EAP status cannot be changed from %s to %s.")
                % (EAPRegistration.Status(current_status).label, EAPRegistration.Status(new_status).label)
            )

        # NOTE: IFRC Admins should be able to transition from TECHNICALLY_VALIDATED
        # to NS_ADDRESSING_COMMENTS to allow NS users to update their EAP changes after validated budget has been set.
        if (current_status, new_status) in [
            (EAPRegistration.Status.UNDER_REVIEW, EAPRegistration.Status.NS_ADDRESSING_COMMENTS),
            (EAPRegistration.Status.TECHNICALLY_VALIDATED, EAPRegistration.Status.NS_ADDRESSING_COMMENTS),
        ]:
            if not is_user_ifrc_admin(user):
                raise PermissionDenied(
                    gettext("You do not have permission to change status to %s.") % EAPRegistration.Status(new_status).label
                )

            review_checklist_file = validated_data.get("review_checklist_file")
            if not review_checklist_file:
                raise serializers.ValidationError(
                    gettext("Review checklist file must be uploaded before changing status to %s.")
                    % EAPRegistration.Status(new_status).label
                )

            # latest EAP
            if self.instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
                snapshot_instance = self.instance.latest_simplified_eap.generate_snapshot()
                self.instance.latest_simplified_eap = snapshot_instance
                snapshot_instance.review_checklist_file = review_checklist_file
                snapshot_instance.save(update_fields=["review_checklist_file"])
                self.instance.save(update_fields=["latest_simplified_eap"])
            else:
                snapshot_instance = self.instance.latest_full_eap.generate_snapshot()
                self.instance.latest_full_eap = snapshot_instance
                self.instance.save(update_fields=["latest_full_eap"])

        elif (current_status, new_status) == (
            EAPRegistration.Status.UNDER_REVIEW,
            EAPRegistration.Status.TECHNICALLY_VALIDATED,
        ):
            if not is_user_ifrc_admin(user):
                raise PermissionDenied(
                    gettext("You do not have permission to change status to %s.") % EAPRegistration.Status(new_status).label
                )

            # Update timestamp
            self.instance.technically_validated_at = timezone.now()
            self.instance.save(
                update_fields=[
                    "technically_validated_at",
                ]
            )

        elif (current_status, new_status) == (
            EAPRegistration.Status.NS_ADDRESSING_COMMENTS,
            EAPRegistration.Status.UNDER_REVIEW,
        ):
            if not (has_country_permission(user, self.instance.national_society_id) or is_user_ifrc_admin(user)):
                raise PermissionDenied(
                    gettext("You do not have permission to change status to %s.") % EAPRegistration.Status(new_status).label
                )

            # Check latest EAP has NS Addressing Comments file uploaded
            if self.instance.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
                if not (self.instance.latest_simplified_eap and self.instance.latest_simplified_eap.updated_checklist_file):
                    raise serializers.ValidationError(
                        gettext("NS Addressing Comments file must be uploaded before changing status to %s.")
                        % EAPRegistration.Status(new_status).label
                    )

                transaction.on_commit(
                    lambda: generate_export_diff_pdf.delay(
                        eap_registration_id=self.instance.id,
                        version=self.instance.latest_simplified_eap.version,
                    )
                )
            else:
                if not (self.instance.latest_full_eap and self.instance.latest_full_eap.updated_checklist_file):
                    raise serializers.ValidationError(
                        gettext("NS Addressing Comments file must be uploaded before changing status to %s.")
                        % EAPRegistration.Status(new_status).label
                    )

                transaction.on_commit(
                    lambda: generate_export_diff_pdf.delay(
                        eap_registration_id=self.instance.id,
                        version=self.instance.latest_full_eap.version,
                    )
                )

        elif (current_status, new_status) == (
            EAPRegistration.Status.TECHNICALLY_VALIDATED,
            EAPRegistration.Status.PENDING_PFA,
        ):
            if not is_user_ifrc_admin(user):
                raise PermissionDenied(
                    gettext("You do not have permission to change status to %s.") % EAPRegistration.Status(new_status).label
                )

            if not self.instance.validated_budget_file:
                raise serializers.ValidationError(
                    gettext("Validated budget file must be uploaded before changing status to %s.")
                    % EAPRegistration.Status(new_status).label
                )

            # Update timestamp
            self.instance.pending_pfa_at = timezone.now()
            self.instance.save(
                update_fields=[
                    "pending_pfa_at",
                ]
            )

        elif (current_status, new_status) == (
            EAPRegistration.Status.PENDING_PFA,
            EAPRegistration.Status.APPROVED,
        ):
            # Update timestamp
            self.instance.approved_at = timezone.now()
            self.instance.save(
                update_fields=[
                    "approved_at",
                ]
            )

            # Generate summary eap for full eap
            if self.instance.get_eap_type_enum == EAPType.FULL_EAP:
                transaction.on_commit(lambda: generate_eap_summary_pdf.delay(self.instance.id))

        elif (current_status, new_status) == (
            EAPRegistration.Status.APPROVED,
            EAPRegistration.Status.ACTIVATED,
        ):
            # Update timestamp
            self.instance.activated_at = timezone.now()
            self.instance.save(
                update_fields=[
                    "activated_at",
                ]
            )
        return validated_data

    def validate(self, validated_data: dict[str, typing.Any]) -> dict[str, typing.Any]:
        self._validate_status(validated_data)
        return validated_data

    def validate_review_checklist_file(self, file):
        if file is None:
            return

        validate_file_extention(file.name, ALLOWED_FILE_EXTENTIONS)
        validate_file_type(file)

        return file
