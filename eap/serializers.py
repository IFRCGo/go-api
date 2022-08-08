from django.utils.translation import ugettext

from rest_framework import serializers

from api.serializers import (
    UserNameSerializer,
    DisasterTypeSerializer,
    CountrySerializer,
    MiniDistrictSerializer,
)

from eap.models import (
    EAP,
    Action,
    EAPPartner,
    EAPReference,
    EarlyAction,
    EarlyActionIndicator,
    EAPDocument,
    PrioritizedRisk,
    EAPActivation,
    EAPOperationalPlan,
    ActionAchievement,
    EAPActivationReport,
    OperationalPlanIndicator,
)

from main.writable_nested_serializers import (
    NestedCreateMixin,
    NestedUpdateMixin,
)


class EAPReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EAPReference
        fields = '__all__'
        read_only_fields = ('eap',)


class EAPPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = EAPPartner
        fields = '__all__'
        read_only_fields = ('eap',)


class EarlyActionIndicatorSerializer(serializers.ModelSerializer):
    indicator_display = serializers.CharField(source='get_indicator_display', read_only=True)

    class Meta:
        model = EarlyActionIndicator
        fields = '__all__'


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ('__all__')
        read_only_fields = ('early_action',)


class PrioritizedRiskSerializer(serializers.ModelSerializer): 
    class Meta:
        model = PrioritizedRisk
        fields = ('__all__')
        read_only_fields = ('early_action',)


class EarlyActionSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    indicators = EarlyActionIndicatorSerializer(many=True, required=False)
    actions = ActionSerializer(source='action', many=True, required=False)
    prioritized_risks = PrioritizedRiskSerializer(source='early_actions_prioritized_risk', many=True, required=False)
    sector_display = serializers.CharField(source='get_sector_display', read_only=True)

    class Meta:
        model = EarlyAction
        fields = ('__all__')


class EAPActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ('__all__')
        read_only_fields = ('early_action',)


class EAPDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = EAPDocument
        fields = ['id', 'file']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class EAPSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    country_details = CountrySerializer(source='country', read_only=True)
    districts_details = MiniDistrictSerializer(source='districts', many=True, read_only=True)
    references = EAPReferenceSerializer(source='eap_reference', many=True, required=False)
    partners = EAPPartnerSerializer(source='eap_partner', many=True, required=False)
    early_actions = EarlyActionSerializer(many=True)
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    modified_by_details = UserNameSerializer(source='modified_by', read_only=True)
    hazard_type_details = DisasterTypeSerializer(source='disaster_type', read_only=True)
    documents_details = EAPDocumentSerializer(source='documents', many=True, read_only=True, required=False)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = EAP
        fields = [
            "id",
            "created_at",
            "modified_at",
            "eap_number",
            "approval_date",
            "status",
            "operational_timeframe",
            "lead_time",
            "eap_timeframe",
            "num_of_people",
            "total_budget",
            "readiness_budget",
            "pre_positioning_budget",
            "early_action_budget",
            "trigger_statement",
            "overview",
            "originator_name",
            "originator_title",
            "originator_email",
            "originator_phone",
            "nsc_name",
            "nsc_title",
            "nsc_email",
            "nsc_phone",
            "ifrc_focal_name",
            "ifrc_focal_title",
            "ifrc_focal_email",
            "ifrc_focal_phone",
            "created_by",
            "created_by_details",
            "modified_by",
            "modified_by_details",
            "country",
            "country_details",
            # "districts",
            "districts_details",
            "disaster_type",
            "hazard_type_details",
            "status_display",
            "references",
            "partners",
            "documents",
            "documents_details",
            "early_actions",
        ]

    def validate(self, validated_data):
        if self.partial:
            return validated_data
        districts = validated_data.get('districts', None)
        if districts:
            for district in districts:
                if district.country != validated_data['country']:
                    raise serializers.ValidationError({
                        'district': ugettext('Different districts found for given country')
                    })
        return validated_data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        eap = super().create(validated_data)
        return eap

    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.context['request'].user
        eap = super().update(instance, validated_data)
        return eap


class EAPActivationSerializer(serializers.ModelSerializer):
    document_detail = EAPDocumentSerializer(source='document', read_only=True)

    class Meta:
        model = EAPActivation
        exclude = ('eap', 'field_report')


class ActionAchievementSerializer(serializers.ModelSerializer):

    class Meta:
        model = ActionAchievement
        exclude = ('operational_plan',)


class OperationalPlanIndicatorSerializer(serializers.ModelSerializer):

    class Meta:
        model = OperationalPlanIndicator
        exclude = ('operational_plan',)


class OperationalPlanSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    indicators = OperationalPlanIndicatorSerializer(source='operational_plan_indicator', many=True, required=False)
    early_actions_achievements = ActionAchievementSerializer(source='action_achievement', many=True, required=False)

    class Meta:
        model = EAPOperationalPlan
        fields = ('__all__')


class EAPActivationReportSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    operational_plans = OperationalPlanSerializer(many=True)
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    modified_by_details = UserNameSerializer(source='modified_by', read_only=True)
    document_details = EAPDocumentSerializer(source='documents', read_only=True, many=True, required=False)
    ifrc_financial_report_details = EAPDocumentSerializer(source='ifrc_financial_report', read_only=True)

    class Meta:
        model = EAPActivationReport
        fields = '__all__'

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        final_report = super().create(validated_data)
        return final_report

    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.context['request'].user
        final_report = super().update(instance, validated_data)
        return final_report
