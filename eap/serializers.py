from django.utils.translation import ugettext

from rest_framework import serializers

from enumfields.drf.serializers import EnumSupportSerializerMixin

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
    class Meta:
        model = EarlyActionIndicator
        fields = ('__all__')


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ('__all__')
        read_only_fields = ('early_action',)


class EarlyActionSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    indicators = EarlyActionIndicatorSerializer(many=True, required=False)
    actions = ActionSerializer(source='action', many=True, required=False)
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
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    file = serializers.FileField(required=False)

    class Meta:
        model = EAPDocument
        fields = '__all__'
        read_only_fields = ('created_by',)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class EAPSerializer(
    EnumSupportSerializerMixin,
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    country_details = CountrySerializer(source='country', read_only=True)
    district_details = MiniDistrictSerializer(source='district', read_only=True)
    references = EAPReferenceSerializer(source='eap_reference', many=True, required=False)
    partners = EAPPartnerSerializer(source='eap_partner', many=True, required=False)
    early_actions = EarlyActionSerializer(many=True)
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    hazard_type_details = DisasterTypeSerializer(source='disaster_type', read_only=True)
    document_details = EAPDocumentSerializer(source='document', read_only=True, required=False)

    class Meta:
        model = EAP
        fields = '__all__'

    def validate(self, validated_data):
        district = validated_data['district']
        if district:
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

