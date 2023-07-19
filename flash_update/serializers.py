from django.db import transaction
from django.utils.translation import gettext

from rest_framework import serializers

from .tasks import share_flash_update, send_flash_update_email

from api.serializers import (
    UserNameSerializer,
    DisasterTypeSerializer,
    CountrySerializer,
    MiniDistrictSerializer,
)
from flash_update.models import (
    FlashReferences,
    FlashUpdate,
    FlashCountryDistrict,
    FlashGraphicMap,
    FlashAction,
    FlashActionsTaken,
    DonorGroup,
    Donors,
    FlashUpdateShare,
)

from main.writable_nested_serializers import (
    NestedCreateMixin,
    NestedUpdateMixin,
)


class DonorGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonorGroup
        fields = '__all__'


class DonorsSerializer(serializers.ModelSerializer):
    groups_details = DonorGroupSerializer(source='groups', many=True, required=False, read_only=True)

    class Meta:
        model = Donors
        fields = '__all__'


class FlashGraphicMapSerializer(serializers.ModelSerializer):
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    file = serializers.FileField(required=False)

    class Meta:
        model = FlashGraphicMap
        fields = '__all__'
        read_only_fields = ('created_by',)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class FlashActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlashAction
        fields = ('name', 'id', 'organizations', 'category', 'tooltip_text', 'client_id')


class FlashActionsTakenSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    action_details = FlashActionSerializer(source='actions', many=True, required=False, read_only=True)
    organization_display = serializers.CharField(source='get_organization_display', read_only=True)

    class Meta:
        model = FlashActionsTaken
        fields = ('organization', 'organization_display', 'actions', 'action_details', 'summary', 'id', 'client_id')
        read_only_fields = ('flash_update',)


class FlashReferencesSerializer(
    serializers.ModelSerializer
):
    document_details = FlashGraphicMapSerializer(source='document', read_only=True)

    class Meta:
        model = FlashReferences
        fields = '__all__'


class FlashCountryDistrictSerializer(serializers.ModelSerializer):
    country_details = CountrySerializer(source='country', read_only=True)
    district_details = MiniDistrictSerializer(source='district', many=True, read_only=True)

    class Meta:
        model = FlashCountryDistrict
        fields = ('id', 'country', 'district', 'country_details', 'district_details', 'client_id')
        read_only_fields = ('flash_update',)

    def validate(self, data):
        districts = data['district']
        if districts:
            for district in districts:
                if district.country != data['country']:
                    raise serializers.ValidationError({
                        'district': gettext('Different districts found for given country')
                    })
        return data


class FlashUpdateSerializer(
    
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    country_district = FlashCountryDistrictSerializer(source='flash_country_district', many=True, required=False)
    references = FlashReferencesSerializer(many=True, required=False)
    actions_taken = FlashActionsTakenSerializer(source='actions_taken_flash', many=True, required=False)
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    hazard_type_details = DisasterTypeSerializer(source='hazard_type', read_only=True)
    share_with_display = serializers.CharField(source='get_share_with_display', read_only=True)
    map_files = FlashGraphicMapSerializer(source='map', many=True, required=False)
    graphics_files = FlashGraphicMapSerializer(source='graphics', many=True, required=False)

    class Meta:
        model = FlashUpdate
        fields = '__all__'

    def validate_country_district(self, attrs):
        if len(attrs) > 10:
            raise serializers.ValidationError("Number of countries selected should not be greater than 10")
        # check for dublicate country
        country_list = []
        for country_district in attrs:
            country_list.append(country_district['country'])
        if len(country_list) > len(set(country_list)):
            raise serializers.ValidationError("Dublicate country selected")

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        flash_update = super().create(validated_data)
        transaction.on_commit(
            lambda: send_flash_update_email.delay(flash_update.id)
        )
        return flash_update

    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.context['request'].user
        flash_update = super().update(instance, validated_data)
        transaction.on_commit(
            lambda: send_flash_update_email.delay(flash_update.id)
        )
        return flash_update


class ShareFlashUpdateSerializer(serializers.ModelSerializer):
    groups_details = DonorGroupSerializer(source='donor_groups', many=True, required=False, read_only=True)
    donors_details = DonorsSerializer(source='donors', many=True, required=False, read_only=True)
    flash_update_details = FlashUpdateSerializer(source='flash_update', required=False, read_only=True)

    class Meta:
        model = FlashUpdateShare
        fields = '__all__'

    def create(self, validated_data):
        flash_update_share = super().create(validated_data)
        transaction.on_commit(
            lambda: share_flash_update.delay(flash_update_share.id)
        )
        return flash_update_share


class ExportFlashUpdateViewSerializer(serializers.Serializer):
    status = serializers.CharField()
    url = serializers.CharField(allow_null=True)
