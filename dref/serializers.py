from django.utils.translation import ugettext

from rest_framework import serializers

from lang.serializers import ModelSerializer
from enumfields.drf.serializers import EnumSupportSerializerMixin
from dref.writable_nested_serializers import (
    NestedCreateMixin,
    NestedUpdateMixin
)
from api.serializers import UserNameSerializer

from dref.models import (
    Dref,
    PlannedIntervention,
    NationalSocietyAction,
    IdentifiedNeed,
    DrefCountryDistrict,
    DrefFile
)


class PlannedInterventionSerializer(ModelSerializer):

    class Meta:
        model = PlannedIntervention
        fields = '__all__'


class NationalSocietyActionSerializer(ModelSerializer):

    class Meta:
        model = NationalSocietyAction
        fields = '__all__'


class IdentifiedNeedSerializer(ModelSerializer):
    class Meta:
        model = IdentifiedNeed
        fields = '__all__'


class DrefCountryDistrictSerializer(ModelSerializer):
    class Meta:
        model = DrefCountryDistrict
        fields = ('id', 'country', 'district')
        read_only_fields = ('dref',)

    def validate(sel, data):
        districts = data['district']
        if isinstance(districts, list) and len(districts):
            for district in districts:
                if district.country != data['country']:
                    raise serializers.ValidationError({
                        'district': ugettext('Different districts found for given country')
                    })
        return data


class DrefFileSerializer(ModelSerializer):
    created_by_details = UserNameSerializer(source='created_by', read_only=True)

    class Meta:
        model = DrefFile
        fields = '__all__'
        read_only_fields = ('created_by',)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DrefSerializer(
    EnumSupportSerializerMixin,
    NestedUpdateMixin,
    NestedCreateMixin,
    ModelSerializer
):
    MAX_NUMBER_OF_IMAGES = 6
    country_district = DrefCountryDistrictSerializer(source='drefcountrydistrict_set', many=True, required=False)
    national_society_actions = NationalSocietyActionSerializer(many=True, required=False)
    needs_identified = IdentifiedNeedSerializer(many=True, required=False)
    planned_interventions = PlannedInterventionSerializer(many=True, required=False)
    type_of_onset_display = serializers.CharField(source='get_type_of_onset_display', read_only=True)
    disaster_category_level_display = serializers.CharField(source='get_disaster_category_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    modified_by_details = UserNameSerializer(source='modified_by', read_only=True)
    event_map_details = DrefFileSerializer(source='event_map', read_only=True)
    images_details = DrefFileSerializer(source='images', many=True, read_only=True)

    class Meta:
        model = Dref
        fields = '__all__'
        read_only_fields = ('modified_by',)

    def validate(self, data):
        event_date = data.get('event_date', None)
        if event_date and data['type_of_onset'] not in [Dref.OnsetType.SLOW, Dref.OnsetType.SUDDEN]:
            raise serializers.ValidationError({
                'event_date': ugettext('Cannot add event_date if onset type not in {} or {}')
                .format(Dref.OnsetType.SLOW.label, Dref.OnsetType.SUDDEN.label)
            })
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {'end_date': 'End date must occur after start date'}
            )
        return data

    def validate_images(self, images):
        if self.instance and images:
            current_images = Dref.objects.filter(id=self.instance.id, images__isnull=False)
            if current_images:
                current_images_id = [image.id for current_image in current_images for image in current_image.images.all()]
                current_images_file = [image.file for current_image in current_images for image in current_image.images.all()]
                for image in images:
                    if image.id in current_images_id:
                        if image.file in current_images_file:
                            continue
                    elif image.created_by != self.context['request'].user:
                        raise serializers.ValidationError(ugettext(
                            'Only image owner can attach image id: {}').format(image.id)
                        )
        if len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(ugettext('Can add utmost {} images').format(self.MAX_NUMBER_OF_IMAGES))
        return images

    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.context['request'].user
        return super().update(instance, validated_data)
