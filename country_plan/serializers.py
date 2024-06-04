from rest_framework import serializers

from utils.file_check import validate_file_type

from .models import CountryPlan, MembershipCoordination, StrategicPriority


class StrategicPrioritySerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = StrategicPriority
        fields = (
            "id",
            "country_plan",
            "type",
            "type_display",
            "funding_requirement",
            "people_targeted",
        )


# NOTE: Defined to be used with CountryPlanViewset
class MembershipCoordinationSerializer(serializers.ModelSerializer):
    sector_display = serializers.CharField(source="get_sector_display", read_only=True)
    national_society_name = serializers.CharField(read_only=True)

    class Meta:
        model = MembershipCoordination
        fields = (
            "id",
            "country_plan",
            "national_society",
            "national_society_name",
            "sector",
            "sector_display",
            "has_coordination",
        )


# NOTE: Defined to be used with CountryPlanViewset
class CountryPlanSerializer(serializers.ModelSerializer):
    strategic_priorities = StrategicPrioritySerializer(source="country_plan_sp", many=True, read_only=True)
    membership_coordinations = MembershipCoordinationSerializer(source="full_country_plan_mc", many=True, read_only=True)
    internal_plan_file = serializers.SerializerMethodField()

    class Meta:
        model = CountryPlan
        fields = (
            "country",
            "internal_plan_file",
            "public_plan_file",
            "requested_amount",
            "people_targeted",
            "is_publish",
            # Manual Defined
            "strategic_priorities",
            "membership_coordinations",
        )

    def get_internal_plan_file(self, obj):
        file = obj.internal_plan_file
        request = self.context["request"]
        if request.user.is_authenticated and file.name:
            return request.build_absolute_uri(serializers.FileField().to_representation(file))

    def validate_internal_plan_file(self, internal_plan_file):
        validate_file_type(internal_plan_file)
        return internal_plan_file

    def validate_public_plan_file(self, public_plan_file):
        validate_file_type(public_plan_file)
        return public_plan_file
