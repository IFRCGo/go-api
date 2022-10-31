from django.utils.translation import ugettext

from rest_framework import serializers

from api.serializers import (
    UserNameSerializer,
    DisasterTypeSerializer,
    CountrySerializer,
    MiniDistrictSerializer,
)
from api.models import District

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
        fields = ['id', 'file', 'caption', ]

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
    documents = EAPDocumentSerializer(many=True, required=False)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = EAP
        fields = ('__all__')

    def validate(self, data):
        if 'districts' in data:
            districts = data.get('districts') or []
            country = data.get('country')
            for district in districts:
                if district.country != country:
                    raise serializers.ValidationError({
                        'districts': ugettext('Different districts found for given country')
                    })
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class EAPActivationSerializer(serializers.ModelSerializer):
    document_details = serializers.SerializerMethodField('get_eap_documents')

    @staticmethod
    def get_eap_documents(obj):
        eap_documents = obj.documents.all()
        return [
            {
                'id': document.id,
                'file': document.file.url,
                'caption': document.caption
            } for document in eap_documents
        ]

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
    documents = EAPDocumentSerializer(many=True, required=False)
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
