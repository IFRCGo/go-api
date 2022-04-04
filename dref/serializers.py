import os

from django.utils.translation import ugettext
from django.db import models
from django.shortcuts import get_object_or_404


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
    DrefFile,
    DrefOperationalUpdate
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
                'event_date': ugettext('Cannot add event_date if onset type not in %s or %s' % (Dref.OnsetType.SLOW.label, Dref.OnsetType.SUDDEN.label))
            })
        if self.instance and self.instance.is_published:
            raise serializers.ValidationError('Published Dref can\'t be changed. Please contact Admin')
        return data

    def validate_images(self, images):
        # Don't allow images more than MAX_NUMBER_OF_IMAGES
        if len(images) > self.MAX_NUMBER_OF_IMAGES:
            raise serializers.ValidationError(
                ugettext('Can add utmost %s images' % self.MAX_NUMBER_OF_IMAGES)
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
                ugettext(
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


class DrefOperationalUpdateSerializer(serializers.ModelSerializer):
    national_society_actions = NationalSocietyActionSerializer(many=True, required=False)
    needs_identified = IdentifiedNeedSerializer(many=True, required=False)
    planned_interventions = PlannedInterventionSerializer(many=True, required=False)
    type_of_onset_display = serializers.CharField(source='get_type_of_onset_display', read_only=True)
    disaster_category_display = serializers.CharField(source='get_disaster_category_display', read_only=True)
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    images_details = DrefFileSerializer(source='images', many=True, read_only=True)
    modified_by_details = UserNameSerializer(source='modified_by', read_only=True)
    country_details = CountrySerializer(source='country', read_only=True)
    district_details = MiniDistrictSerializer(source='district', read_only=True, many=True)

    class Meta:
        model = DrefOperationalUpdate
        fields = '__all__'
        read_only_fields = ('dref',)

    def validate(self, data):
        data['dref_id'] = int(self.context['dref_id'])
        dref = get_object_or_404(Dref, id=data['dref_id'])
        if not dref.is_published:
            raise serializers.ValidationError(
                ugettext('Can\'t create Operational Update for not publised %s dref.' % dref.id)
            )
        operational_parent = data.get('parent')
        if operational_parent and not operational_parent.is_published:
            raise serializers.ValidationError(
                ugettext('Can\'t create Operational Update for whose %s parent is not published.' % operational_parent.id)
            )
        return data

    def create(self, validated_data):
        dref_id = self.context["dref_id"]
        dref = Dref.objects.get(pk=dref_id)
        dref_country_district = get_object_or_404(DrefCountryDistrict, dref=dref)
        validated_data['title'] = dref.title
        validated_data['national_society'] = dref.national_society
        validated_data['disaster_type'] = dref.disaster_type
        validated_data['type_of_onset'] = dref.type_of_onset
        validated_data['disaster_category'] = dref.disaster_category
        validated_data['number_of_people_targated'] = dref.total_targeted_population
        validated_data['number_of_people_affected'] = dref.num_affected
        validated_data['emergency_appeal_planned'] = dref.emergency_appeal_planned
        validated_data['images'] = dref.images.all()
        validated_data['appeal_code'] = dref.appeal_code
        validated_data['glide_code'] = dref.glide_code
        validated_data['ifrc_appeal_manager_name'] = dref.ifrc_appeal_manager_name
        validated_data['ifrc_appeal_manager_email'] = dref.ifrc_appeal_manager_email
        validated_data['ifrc_appeal_manager_title'] = dref.ifrc_appeal_manager_title
        validated_data['ifrc_appeal_manager_phone_number'] = dref.ifrc_appeal_manager_phone_number
        validated_data['ifrc_project_manager_name'] = dref.ifrc_project_manager_name
        validated_data['ifrc_project_manager_email'] = dref.ifrc_project_manager_email
        validated_data['ifrc_project_manager_title'] = dref.ifrc_project_manager_title
        validated_data['ifrc_project_manager_phone_number'] = dref.ifrc_project_manager_phone_number
        validated_data['national_society_contact_name'] = dref.national_society_contact_name
        validated_data['national_society_contact_email'] = dref.national_society_contact_email
        validated_data['national_society_contact_title'] = dref.national_society_contact_title
        validated_data['national_society_contact_phone_number'] = dref.national_society_contact_phone_number
        validated_data['media_contact_name'] = dref.media_contact_name
        validated_data['media_contact_email'] = dref.media_contact_email
        validated_data['media_contact_title'] = dref.media_contact_title
        validated_data['media_contact_phone_number'] = dref.media_contact_phone_number
        validated_data['ifrc_emergency_name'] = dref.ifrc_emergency_name
        validated_data['ifrc_emergency_title'] = dref.ifrc_emergency_title
        validated_data['ifrc_emergency_phone_number'] = dref.ifrc_emergency_phone_number
        validated_data['ifrc_emergency_email'] = dref.ifrc_emergency_email
        validated_data['national_society_actions'] = dref.national_society_actions.all()
        validated_data['ifrc'] = dref.ifrc
        validated_data['icrc'] = dref.icrc
        validated_data['partner_national_society'] = dref.partner_national_society
        validated_data['government_requested_assistance'] = dref.government_requested_assistance
        validated_data['national_authorities'] = dref.national_authorities
        validated_data['un_or_other_actor'] = dref.un_or_other_actor
        validated_data['major_coordination_mechanism'] = dref.major_coordination_mechanism
        validated_data['needs_identified'] = dref.needs_identified.all()
        validated_data['people_assisted'] = dref.people_assisted
        validated_data['selection_criteria'] = dref.selection_criteria
        validated_data['women'] = dref.women
        validated_data['men'] = dref.men
        validated_data['girls'] = dref.girls
        validated_data['boys'] = dref.boys
        validated_data['disability_people_per'] = dref.disability_people_per
        validated_data['people_per_urban'] = dref.people_per_urban
        validated_data['people_per_local'] = dref.people_per_local
        validated_data['people_targeted_with_early_actions'] = dref.people_targeted_with_early_actions
        validated_data['displaced_people'] = dref.displaced_people
        validated_data['operation_objective'] = dref.operation_objective
        validated_data['response_strategy'] = dref.response_strategy
        validated_data['planned_interventions'] = dref.planned_interventions.all()
        validated_data['country'] = dref_country_district.country
        validated_data['district'] = dref_country_district.district.all()
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
