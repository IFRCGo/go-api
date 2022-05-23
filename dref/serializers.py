import os

from django.utils.translation import gettext
from django.db import models

from rest_framework import serializers

from lang.serializers import ModelSerializer
from main.writable_nested_serializers import (
    NestedCreateMixin,
    NestedUpdateMixin
)
from api.serializers import (
    UserNameSerializer,
    MiniFieldReportSerializer,
    DisasterTypeSerializer,
    CountrySerializer,
    MiniDistrictSerializer,
)

from dref.models import (
    Dref,
    PlannedIntervention,
    NationalSocietyAction,
    IdentifiedNeed,
    DrefCountryDistrict,
    DrefFile
)


class DrefFileSerializer(ModelSerializer):
    created_by_details = UserNameSerializer(source='created_by', read_only=True)

    class Meta:
        model = DrefFile
        fields = '__all__'
        read_only_fields = ('created_by',)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PlannedInterventionSerializer(ModelSerializer):
    budget_file_details = DrefFileSerializer(source='budget_file', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PlannedIntervention
        fields = '__all__'

    def get_image_url(self, plannedintervention):
        request = self.context['request']
        title = plannedintervention.title
        if title:
            return PlannedIntervention.get_image_map(title, request)
        return None


class NationalSocietyActionSerializer(ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = NationalSocietyAction
        fields = (
            'id',
            'title',
            'description',
            'image_url',
        )

    def get_image_url(self, nationalsocietyactions):
        request = self.context['request']
        title = nationalsocietyactions.title
        if title:
            return NationalSocietyAction.get_image_map(title, request)
        return None


class IdentifiedNeedSerializer(ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = IdentifiedNeed
        fields = (
            'id',
            'title',
            'description',
            'image_url',
        )

    def get_image_url(self, identifiedneed):
        request = self.context['request']
        title = identifiedneed.title
        if title:
            return IdentifiedNeed.get_image_map(title, request)
        return None


class DrefCountryDistrictSerializer(ModelSerializer):
    country_details = CountrySerializer(source='country', read_only=True)
    district_details = MiniDistrictSerializer(source='district', read_only=True, many=True)

    class Meta:
        model = DrefCountryDistrict
        fields = ('id', 'country', 'district', 'country_details', 'district_details')
        read_only_fields = ('dref',)

    def validate(self, data):
        districts = data['district']
        if isinstance(districts, list) and len(districts):
            for district in districts:
                if district.country != data['country']:
                    raise serializers.ValidationError({
                        'district': gettext('Different districts found for given country')
                    })
        return data


class DrefSerializer(
    
    NestedUpdateMixin,
    NestedCreateMixin,
    ModelSerializer
):
    MAX_NUMBER_OF_IMAGES = 6
    ALLOWED_BUDGET_FILE_EXTENSIONS = ["pdf"]

    country_district = DrefCountryDistrictSerializer(source='drefcountrydistrict_set', many=True, required=False)
    national_society_actions = NationalSocietyActionSerializer(many=True, required=False)
    needs_identified = IdentifiedNeedSerializer(many=True, required=False)
    planned_interventions = PlannedInterventionSerializer(many=True, required=False)
    type_of_onset_display = serializers.CharField(source='get_type_of_onset_display', read_only=True)
    disaster_category_display = serializers.CharField(source='get_disaster_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    modified_by_details = UserNameSerializer(source='modified_by', read_only=True)
    event_map_details = DrefFileSerializer(source='event_map', read_only=True)
    images_details = DrefFileSerializer(source='images', many=True, read_only=True)
    field_report_details = MiniFieldReportSerializer(source='field_report', read_only=True)
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    users_details = UserNameSerializer(source='users', many=True, read_only=True)
    budget_file_details = DrefFileSerializer(source='budget_file', read_only=True)
    cover_image_details = DrefFileSerializer(source='cover_image', read_only=True)
    disaster_type_details = DisasterTypeSerializer(source='disaster_type', read_only=True)

    class Meta:
        model = Dref
        fields = '__all__'
        read_only_fields = ('modified_by', 'created_by', 'budget_file_preview')

    def to_representation(self, instance):
        def _remove_digits_after_decimal(value):
            # NOTE: We are doing this to remove decimal after 3 digits whole numbers
            # eg: 100.00% be replaced with 100%
            if value and len(value.split('.')[0]) == 3:
                return value.split('.')[0]
            return None

        data = super().to_representation(instance)
        for key in [
            'disability_people_per',
            'people_per_urban',
            'people_per_local',
        ]:
            value = data.get(key) or ''
            data[key] = _remove_digits_after_decimal(value)
        return data

    def validate(self, data):
        event_date = data.get('event_date')
        if event_date and data['type_of_onset'] not in [Dref.OnsetType.SLOW, Dref.OnsetType.SUDDEN]:
            raise serializers.ValidationError({
                'event_date': gettext('Cannot add event_date if onset type not in %s or %s' % (Dref.OnsetType.SLOW.label, Dref.OnsetType.SUDDEN.label))
            })
        return data

    def validate_images(self, images):
        # Don't allow images more than MAX_NUMBER_OF_IMAGES
        if len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(
                gettext('Can add utmost %s images' % self.MAX_NUMBER_OF_IMAGES)
            )
        images_id = [image.id for image in images]
        images_without_access_qs = DrefFile.objects.filter(
            # Not created by current user
            ~models.Q(created_by=self.context['request'].user),
            # Look into provided images
            id__in=images_id,
        )
        # Exclude already attached images if exists
        if self.instance:
            images_without_access_qs = images_without_access_qs.exclude(
                id__in=self.instance.images.all()
            )
        images_id_without_access = images_without_access_qs.values_list('id', flat=True)
        if images_id_without_access:
            raise serializers.ValidationError(
                gettext(
                    'Only image owner can attach image. Not allowed image ids: %s' % ','.join(map(str, images_id_without_access))
                )
            )
        return images

    def validate_budget_file(self, budget_file):
        if budget_file is None:
            return
        extension = os.path.splitext(budget_file.file.name)[1].replace(".", "")
        if extension.lower() not in self.ALLOWED_BUDGET_FILE_EXTENSIONS:
            raise serializers.ValidationError(
                f'Invalid uploaded file extension: {extension}, Supported only PDF Files'
            )
        return budget_file

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.context['request'].user
        return super().update(instance, validated_data)
