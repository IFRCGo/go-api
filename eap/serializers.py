from rest_framework import serializers

from api.serializers import MiniCountrySerializer, UserNameSerializer
from eap.models import EAPRegistration
from main.writable_nested_serializers import NestedCreateMixin, NestedUpdateMixin


class EAPRegistrationSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer,
):
    country_details = MiniCountrySerializer(source="country", read_only=True)
    national_society_details = MiniCountrySerializer(source="national_society", read_only=True)
    partners_details = MiniCountrySerializer(source="partners", many=True, read_only=True)

    eap_type_display = serializers.CharField(source="get_eap_type_display", read_only=True)

    # User details
    created_by_details = UserNameSerializer(source="created_by", read_only=True)
    modified_by_details = UserNameSerializer(source="modified_by", read_only=True)

    # Status
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EAPRegistration
        fields = "__all__"
        read_only_fields = [
            "status",
            "modified_at",
        ]
