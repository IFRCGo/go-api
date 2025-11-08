import typing

from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.serializers import Admin2Serializer, MiniCountrySerializer, UserNameSerializer
from eap.models import (
    EAPFile,
    EAPRegistration,
    EnableApproach,
    OperationActivity,
    PlannedOperations,
    SimplifiedEAP,
)
from main.writable_nested_serializers import NestedCreateMixin, NestedUpdateMixin
from utils.file_check import validate_file_type

User = get_user_model()


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

    # EAPs
    simplified_eap_details = MiniSimplifiedEAPSerializer(source="simplified_eap", read_only=True)

    # Status
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EAPRegistration
        fields = "__all__"
        read_only_fields = [
            "is_active",
            "status",
            "modified_at",
            "created_by",
            "modified_by",
        ]


class EAPFileSerializer(BaseEAPSerializer):
    id = serializers.IntegerField(required=False)
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


class OperationActivitySerializer(
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = OperationActivity
        fields = "__all__"


class PlannedOperationsSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    activities = OperationActivitySerializer(many=True, required=False)

    class Meta:
        model = PlannedOperations
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


class SimplifiedEAPSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    BaseEAPSerializer,
):
    MAX_NUMBER_OF_IMAGES = 5

    planned_operations = PlannedOperationsSerializer(many=True, required=False)
    enable_approach = EnableApproachSerializer(many=False, required=False)

    # FILES
    cover_image_details = EAPFileSerializer(source="cover_image", read_only=True)
    hazard_impact_file_details = EAPFileSerializer(source="hazard_impact_file", many=True, read_only=True)
    selected_early_actions_file_details = EAPFileSerializer(source="selected_early_actions_file", many=True, read_only=True)
    risk_selected_protocols_file_details = EAPFileSerializer(source="risk_selected_protocols_file", many=True, read_only=True)

    # Admin2
    admin2_details = Admin2Serializer(source="admin2", many=True, read_only=True)

    class Meta:
        model = SimplifiedEAP
        fields = "__all__"

    def validate_hazard_impact_file(self, images):
        if images and len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(f"Maximum {self.MAX_NUMBER_OF_IMAGES} images are allowed to upload.")
        return images

    def validate_risk_selected_protocols_file(self, images):
        if images and len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(f"Maximum {self.MAX_NUMBER_OF_IMAGES} images are allowed to upload.")
        return images

    def validate_selected_early_actions_file(self, images):
        if images and len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(f"Maximum {self.MAX_NUMBER_OF_IMAGES} images are allowed to upload.")
        return images


class EAPStatusSerializer(
    BaseEAPSerializer,
):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EAPRegistration
        fields = [
            "id",
            "status_display",
            "status",
        ]

    # TODO(susilnem): Add status state validations
