import typing

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
    EAPFile,
    EAPRegistration,
    EAPType,
    EnableApproach,
    FullEAP,
    KeyActor,
    OperationActivity,
    PlannedOperation,
    SimplifiedEAP,
    SourceInformation,
)
from eap.utils import (
    has_country_permission,
    is_user_ifrc_admin,
    validate_file_extention,
)
from main.writable_nested_serializers import NestedCreateMixin, NestedUpdateMixin
from utils.file_check import validate_file_type

ALLOWED_FILE_EXTENTIONS: list[str] = ["pdf", "docx", "pptx", "xlsx"]


class BaseEAPSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        # NOTE: Setting `created_by` and `modified_by` required to Flase
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

    # Status
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EAPRegistration
        fields = "__all__"
        read_only_fields = [
            "status",
            "validated_budget_file",
            "review_checklist_file",
            "modified_at",
            "created_by",
            "modified_by",
        ]

    def update(self, instance: EAPRegistration, validated_data: dict[str, typing.Any]) -> dict[str, typing.Any]:
        # Cannot update once EAP application is being created.
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

    def validate_file(self, file):
        validate_file_type(file)
        return file


ALLOWED_MAP_TIMEFRAMES_VALUE = {
    OperationActivity.TimeFrame.YEARS: list(OperationActivity.YearsTimeFrameChoices.values),
    OperationActivity.TimeFrame.MONTHS: list(OperationActivity.MonthsTimeFrameChoices.values),
    OperationActivity.TimeFrame.DAYS: list(OperationActivity.DaysTimeFrameChoices.values),
    OperationActivity.TimeFrame.HOURS: list(OperationActivity.HoursTimeFrameChoices.values),
}


class OperationActivitySerializer(
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    timeframe = serializers.ChoiceField(
        choices=OperationActivity.TimeFrame.choices,
        required=True,
    )
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
                    % (invalid_values, OperationActivity.TimeFrame(timeframe).label)
                }
            )
        return validated_data


class PlannedOperationSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)

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


class SourceInformationSerializer(
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


class SimplifiedEAPSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    BaseEAPSerializer,
):
    MAX_NUMBER_OF_IMAGES = 5

    planned_operations = PlannedOperationSerializer(many=True, required=False)
    enable_approaches = EnableApproachSerializer(many=True, required=False)

    # FILES
    cover_image_file = EAPFileUpdateSerializer(source="cover_image", required=False, allow_null=True)
    hazard_impact_images_details = EAPFileSerializer(source="hazard_impact_images", many=True, read_only=True)
    selected_early_actions_file_details = EAPFileSerializer(source="selected_early_actions_images", many=True, read_only=True)
    risk_selected_protocols_file_details = EAPFileSerializer(source="risk_selected_protocols_images", many=True, read_only=True)

    # Admin2
    admin2_details = Admin2Serializer(source="admin2", many=True, read_only=True)

    class Meta:
        model = SimplifiedEAP
        read_only_fields = [
            "version",
            "is_locked",
        ]
        exclude = ("cover_image",)

    def validate_hazard_impact_images(self, images):
        if images and len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(f"Maximum {self.MAX_NUMBER_OF_IMAGES} images are allowed to upload.")
        validate_file_type(images)
        return images

    def validate_risk_selected_protocols_images(self, images):
        if images and len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(f"Maximum {self.MAX_NUMBER_OF_IMAGES} images are allowed to upload.")
        validate_file_type(images)
        return images

    def validate_selected_early_actions_images(self, images):
        if images and len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(f"Maximum {self.MAX_NUMBER_OF_IMAGES} images are allowed to upload.")
        validate_file_type(images)
        return images

    def validate(self, data: dict[str, typing.Any]) -> dict[str, typing.Any]:
        eap_registration: EAPRegistration = data["eap_registration"]

        if not self.instance and eap_registration.has_eap_application:
            raise serializers.ValidationError("Simplified EAP for this EAP registration already exists.")

        # NOTE: Cannot update locked Simplified EAP
        if self.instance and self.instance.is_locked:
            raise serializers.ValidationError("Cannot update locked Simplified EAP.")

        eap_type = eap_registration.get_eap_type_enum
        if eap_type and eap_type != EAPType.SIMPLIFIED_EAP:
            raise serializers.ValidationError("Cannot create Simplified EAP for non-simplified EAP registration.")
        return data

    def create(self, validated_data: dict[str, typing.Any]):
        instance: SimplifiedEAP = super().create(validated_data)
        instance.eap_registration.update_eap_type(EAPType.SIMPLIFIED_EAP)
        return instance


class FullEAPSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    BaseEAPSerializer,
):

    MAX_NUMBER_OF_IMAGES = 5

    planned_operations = PlannedOperationSerializer(many=True, required=False)
    enable_approaches = EnableApproachSerializer(many=True, required=False)
    # admins
    admin2_details = Admin2Serializer(source="admin2", many=True, read_only=True)
    key_actors = KeyActorSerializer(many=True, required=True)

    # SOURCE OF INFOMATIONS
    risk_analysis_source_of_information = SourceInformationSerializer(many=True)
    trigger_statement_source_of_information = SourceInformationSerializer(many=True)
    trigger_model_source_of_information = SourceInformationSerializer(many=True)
    evidence_base_source_of_information = SourceInformationSerializer(many=True)
    activation_process_source_of_information = SourceInformationSerializer(many=True)

    # FILES
    cover_image_details = EAPFileSerializer(source="cover_image", read_only=True)
    hazard_selection_files_details = EAPFileSerializer(source="hazard_selection_files", many=True, read_only=True)
    exposed_element_and_vulnerability_factor_files_details = EAPFileSerializer(
        source="exposed_element_and_vulnerability_factor_files", many=True, read_only=True
    )
    prioritized_impact_files_details = EAPFileSerializer(source="prioritized_impact_files", many=True, read_only=True)
    risk_analysis_relevant_files_details = EAPFileSerializer(source="risk_analysis_relevant_files", many=True, read_only=True)
    forecast_selection_files_details = EAPFileSerializer(source="forecast_selection_files", many=True, read_only=True)
    definition_and_justification_impact_level_files_details = EAPFileSerializer(
        source="definition_and_justification_impact_level_files", many=True, read_only=True
    )
    identification_of_the_intervention_area_files_details = EAPFileSerializer(
        source="identification_of_the_intervention_area_files", many=True, read_only=True
    )
    trigger_model_relevant_files_details = EAPFileSerializer(source="trigger_model_relevant_files", many=True, read_only=True)
    early_action_selection_process_files_details = EAPFileSerializer(
        source="early_action_selection_process_files", many=True, read_only=True
    )
    theory_of_change_table_file_details = EAPFileSerializer(source="theory_of_change_table_file", read_only=True)
    evidence_base_files_details = EAPFileSerializer(source="evidence_base_files", many=True, read_only=True)
    early_action_implementation_files_details = EAPFileSerializer(
        source="early_action_implementation_files", many=True, read_only=True
    )
    trigger_activation_system_files_details = EAPFileSerializer(
        source="trigger_activation_system_files", many=True, read_only=True
    )
    activation_process_relevant_files_details = EAPFileSerializer(
        source="activation_process_relevant_files", many=True, read_only=True
    )
    meal_relevant_files_details = EAPFileSerializer(source="meal_relevant_files", many=True, read_only=True)
    capacity_relevant_files_details = EAPFileSerializer(source="capacity_relevant_files", many=True, read_only=True)

    class Meta:
        model = FullEAP
        fields = "__all__"
        read_only_fields = (
            "created_by",
            "modified_by",
        )


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
        (EAPRegistration.Status.TECHNICALLY_VALIDATED, EAPRegistration.Status.APPROVED),
        (EAPRegistration.Status.APPROVED, EAPRegistration.Status.PFA_SIGNED),
        (EAPRegistration.Status.PFA_SIGNED, EAPRegistration.Status.ACTIVATED),
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

        if (current_status, new_status) == (
            EAPRegistration.Status.UNDER_REVIEW,
            EAPRegistration.Status.NS_ADDRESSING_COMMENTS,
        ):
            if not is_user_ifrc_admin(user):
                raise PermissionDenied(
                    gettext("You do not have permission to change status to %s.") % EAPRegistration.Status(new_status).label
                )

            if not validated_data.get("review_checklist_file"):
                raise serializers.ValidationError(
                    gettext("Review checklist file must be uploaded before changing status to %s.")
                    % EAPRegistration.Status(new_status).label
                )

            # NOTE: Add checks for FULL EAP
            simplified_eap_instance: SimplifiedEAP | None = (
                SimplifiedEAP.objects.filter(eap_registration=self.instance).order_by("-version").first()
            )

            if simplified_eap_instance:
                simplified_eap_instance.generate_snapshot()

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

            latest_simplified_eap: SimplifiedEAP | None = (
                SimplifiedEAP.objects.filter(
                    eap_registration=self.instance,
                )
                .order_by("-version")
                .first()
            )

            # TODO(susilnem): Add checks for FULL EAP
            if not (latest_simplified_eap and latest_simplified_eap.updated_checklist_file):
                raise serializers.ValidationError(
                    gettext("NS Addressing Comments file must be uploaded before changing status to %s.")
                    % EAPRegistration.Status(new_status).label
                )

        elif (current_status, new_status) == (
            EAPRegistration.Status.TECHNICALLY_VALIDATED,
            EAPRegistration.Status.APPROVED,
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
            self.instance.approved_at = timezone.now()
            self.instance.save(
                update_fields=[
                    "approved_at",
                ]
            )

        elif (current_status, new_status) == (
            EAPRegistration.Status.APPROVED,
            EAPRegistration.Status.PFA_SIGNED,
        ):
            # Update timestamp
            self.instance.pfa_signed_at = timezone.now()
            self.instance.save(
                update_fields=[
                    "pfa_signed_at",
                ]
            )

        elif (current_status, new_status) == (
            EAPRegistration.Status.PFA_SIGNED,
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
