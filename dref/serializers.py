import os

from django.utils.translation import ugettext

from rest_framework import serializers

from lang.serializers import ModelSerializer
from enumfields.drf.serializers import EnumSupportSerializerMixin
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
from dref.scripts import pdf_image_extractor


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
                        'district': ugettext('Different districts found for given country')
                    })
        return data


class DrefSerializer(
    EnumSupportSerializerMixin,
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
        data = super().to_representation(instance)
        disability_people_per = data.get('disability_people_per', '')
        if disability_people_per and len(disability_people_per.split('.')[0]) == 3:
            data['disability_people_per'] = disability_people_per.split('.')[0]
        people_per_urban = data.get('people_per_urban', '')
        people_per_local = data.get('people_per_local', '')
        if people_per_urban and len(people_per_urban.split('.')[0]) == 3:
            data['people_per_urban'] = people_per_urban.split('.')[0]
        if people_per_local and len(people_per_local.split('.')[0]) == 3:
            data['people_per_local'] = people_per_local.split('.')[0]
        return data

    def validate(self, data):
        event_date = data.get('event_date', None)
        if event_date and data['type_of_onset'] not in [Dref.OnsetType.SLOW, Dref.OnsetType.SUDDEN]:
            raise serializers.ValidationError({
                'event_date': ugettext('Cannot add event_date if onset type not in {} or {}')
                .format(Dref.OnsetType.SLOW.label, Dref.OnsetType.SUDDEN.label)
            })
        return data

    def validate_images(self, images):
        # Validate if images are provided
        if images:
            # Fetch current images
            current_images_map = {
                image.pk: image.file
                for image in (self.instance and self.instance.images.all()) or []
            }
            for image in images:
                # Ignore for current images (if file is not changed)
                if image.id is not None and image.id in current_images_map and image.file == current_images_map[image.id]:
                    continue
                elif image.created_by != self.context['request'].user:
                    raise serializers.ValidationError(
                        ugettext('Only image owner can attach image(id: %s)' % image.id)
                    )
        # Don't allow images more than MAX_NUMBER_OF_IMAGES
        if len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(
                ugettext('Can add utmost %s images' % self.MAX_NUMBER_OF_IMAGES)
            )
        return images

    def validate_extension(self, filename):
        extension = os.path.splitext(filename)[1].replace(".", "")
        if extension.lower() not in self.ALLOWED_BUDGET_FILE_EXTENSIONS:
            raise serializers.ValidationError(
                f'Invalid uploaded file type: {filename}, Supported only PDF Files'
            )

    def validate_budget_file(self, budget_file):
        if budget_file:
            self.validate_extension(os.path.basename(budget_file.file.name))
        return budget_file

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        budget_file = validated_data.get('budget_file', None)
        if budget_file:
            validated_data['budget_file_preview'] = pdf_image_extractor(budget_file.file.path)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.context['request'].user
        return super().update(instance, validated_data)
