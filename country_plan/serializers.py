from rest_framework import serializers

from .models import (
    CountryPlan,
    StrategicPriority,
    MembershipCoordination,
)


class StrategicPrioritySerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = StrategicPriority
        fields = (
            'id',
            'country_plan',
            'type',
            'type_display',
            'funding_requirement',
            'people_targeted',
        )


# NOTE: Defined to be used with CountryPlanViewset
class MembershipCoordinationSerializer(serializers.ModelSerializer):
    sector_display = serializers.CharField(source='get_sector_display', read_only=True)
    national_society_name = serializers.CharField(read_only=True)  # Generated in CountryPlanViewset.queryset Prefetch

    class Meta:
        model = MembershipCoordination
        fields = (
            'id',
            'country_plan',
            'national_society',
            'national_society_name',
            'sector',
            'sector_display',
            'has_coordination',
        )


# NOTE: Defined to be used with CountryPlanViewset
class CountryPlanSerializer(serializers.ModelSerializer):
    strategic_priorities = StrategicPrioritySerializer(source='country_plan_sp', many=True, read_only=True)
    membership_coordinations = MembershipCoordinationSerializer(source='full_country_plan_mc', many=True, read_only=True)

    class Meta:
        model = CountryPlan
        fields = (
            'country',
            'internal_plan_file',  # TODO: This is internal. When to show?
            'public_plan_file',
            'requested_amount',
            'people_targeted',
            'is_publish',
            # Manual Defined
            'strategic_priorities',
            'membership_coordinations',
        )
