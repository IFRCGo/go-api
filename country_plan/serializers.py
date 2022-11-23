from rest_framework import serializers

from .models import (
    CountryPlan,
    StrategicPriority,
    MembershipCoordination,
)


class StrategicPrioritySerializer(serializers.ModelSerializer):
    sp_name_display = serializers.CharField(source='get_sp_name_display', read_only=True)

    class Meta:
        model = StrategicPriority
        fields = (
            'id',
            'country_plan',
            'sp_name',
            'funding_requirement',
            'people_targeted',
            # Manual Defined
            'sp_name_display',
        )


# NOTE: Defined to be used with CountryPlanViewset
class MembershipCoordinationSerializer(serializers.ModelSerializer):
    # TODO: national_society_display
    strategic_priority_display = serializers.CharField(source='get_strategic_priority_display', read_only=True)
    national_society_name = serializers.CharField(read_only=True)  # Generated in CountryPlanViewset.queryset Prefetch

    class Meta:
        model = MembershipCoordination
        fields = (
            'id',
            'country_plan',
            'national_society',
            'national_society_name',
            'strategic_priority',
            'has_coordination',
            # Manual Defined
            'strategic_priority_display',
        )


# NOTE: Defined to be used with CountryPlanViewset
class CountryPlanSerializer(serializers.ModelSerializer):
    strategic_priorities = StrategicPrioritySerializer(source='country_plan_sp', many=True, read_only=True)
    membership_coordinationes = MembershipCoordinationSerializer(source='country_plan_mc', many=True, read_only=True)

    class Meta:
        model = CountryPlan
        fields = (
            'id',
            'internal_plan_file',  # TODO: This is internal. When to show?
            'public_plan_file',
            'country',
            'requested_amount',
            'people_targeted',
            'situation_analysis',
            'role_of_national_society',
            'is_publish',
            # Manual Defined
            'strategic_priorities',
            'membership_coordinationes',
        )
