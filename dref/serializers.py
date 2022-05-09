import os
import datetime

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
    PlannedInterventionIndicators,
    NationalSocietyAction,
    IdentifiedNeed,
    DrefCountryDistrict,
    DrefFile,
    DrefOperationalUpdate,
    DrefOperationalUpdateCountryDistrict
)


class PlannedInterventionIndicatorsSerializer(ModelSerializer):
    class Meta:
        model = PlannedInterventionIndicators
        fields = '__all__'


class DrefFileSerializer(ModelSerializer):
    created_by_details = UserNameSerializer(source='created_by', read_only=True)

    class Meta:
        model = DrefFile
        fields = '__all__'
        read_only_fields = ('created_by',)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PlannedInterventionSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    ModelSerializer
):
    budget_file_details = DrefFileSerializer(source='budget_file', read_only=True)
    image_url = serializers.SerializerMethodField()
    indicators = PlannedInterventionIndicatorsSerializer(many=True, required=False)
    title_display = serializers.CharField(source='get_title_display', read_only=True)

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
    title_display = serializers.CharField(source='get_title_display', read_only=True)

    class Meta:
        model = NationalSocietyAction
        fields = (
            'id',
            'title',
            'description',
            'image_url',
            'title_display',
        )

    def get_image_url(self, nationalsocietyactions):
        request = self.context['request']
        title = nationalsocietyactions.title
        if title:
            return NationalSocietyAction.get_image_map(title, request)
        return None


class IdentifiedNeedSerializer(ModelSerializer):
    image_url = serializers.SerializerMethodField()
    title_display = serializers.CharField(source='get_title_display', read_only=True)

    class Meta:
        model = IdentifiedNeed
        fields = (
            'id',
            'title',
            'description',
            'image_url',
            'title_display',
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


class DrefOperationalUpdateCountryDistrictSerializer(ModelSerializer):
    country_details = CountrySerializer(source='country', read_only=True)
    district_details = MiniDistrictSerializer(source='district', read_only=True, many=True)

    class Meta:
        model = DrefOperationalUpdateCountryDistrict
        fields = ('id', 'country', 'district', 'country_details', 'district_details')
        read_only_fields = ('dref_operational_update',)

    def validate(self, data):
        districts = data['district']
        if isinstance(districts, list) and len(districts):
            for district in districts:
                if district.country != data['country']:
                    raise serializers.ValidationError({
                        'district': ugettext('Different districts found for given country')
                    })
        return data


class MiniOperationalUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrefOperationalUpdate
        fields = [
            'id',
            'title',
            'is_published',
            'operational_update_number',
        ]


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
    operational_update_details = MiniOperationalUpdateSerializer(source='drefoperationalupdate_set', many=True, read_only=True)

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
            return value

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


class DrefOperationalUpdateSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    national_society_actions = NationalSocietyActionSerializer(many=True, required=False)
    needs_identified = IdentifiedNeedSerializer(many=True, required=False)
    planned_interventions = PlannedInterventionSerializer(many=True, required=False)
    type_of_onset_display = serializers.CharField(source='get_type_of_onset_display', read_only=True)
    disaster_category_display = serializers.CharField(source='get_disaster_category_display', read_only=True)
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    images_details = DrefFileSerializer(source='images', many=True, read_only=True)
    modified_by_details = UserNameSerializer(source='modified_by', read_only=True)
    disaster_type_details = DisasterTypeSerializer(source='disaster_type', read_only=True)
    country_district = DrefOperationalUpdateCountryDistrictSerializer(
        source='drefoperationalupdatecountrydistrict_set',
        many=True,
        required=False
    )

    class Meta:
        model = DrefOperationalUpdate
        fields = '__all__'
        read_only_fields = ('operational_update_number', )

    def validate(self, data):
        dref = data.get('dref')
        if not self.instance and dref:
            dref = get_object_or_404(Dref, id=dref.id)
            if not dref.is_published:
                raise serializers.ValidationError(
                    ugettext('Can\'t create Operational Update for not published %s dref.' % dref.id)
                )
            # get the latest dref_operation_update and check whether it is published or not, exclude no operational object created so far
            operational_update_queryset = DrefOperationalUpdate.objects.filter(dref=dref)
            if not operational_update_queryset.count() == 0:
                dref_operational_update = operational_update_queryset.order_by('-operational_update_number')[0]
                if dref_operational_update and not dref_operational_update.is_published:
                    raise serializers.ValidationError(
                        ugettext(
                            'Can\'t create Operational Update for not published Operational Update %s id and Operational Update Number %i.'
                            % (dref_operational_update.id, dref_operational_update.operational_update_number)
                        )
                    )
        return data

    def get_total_timeframe(self, start_date, end_date):
        if start_date and end_date:
            start_date_month = datetime.datetime.strftime('%m')
            end_date_month = datetime.datetime.strptime('%m')
            return abs(end_date_month - start_date_month)
        return None

    def create(self, validated_data):
        dref = validated_data.get('dref')
        dref_operational_update = DrefOperationalUpdate.objects.filter(dref=dref)
        if dref_operational_update.count() == 0:
            validated_data['title'] = dref.title
            validated_data['national_society'] = dref.national_society
            validated_data['disaster_type'] = dref.disaster_type
            validated_data['type_of_onset'] = dref.type_of_onset
            validated_data['disaster_category'] = dref.disaster_category
            validated_data['number_of_people_targeted'] = dref.num_assisted
            validated_data['number_of_people_affected'] = dref.num_affected
            validated_data['emergency_appeal_planned'] = dref.emergency_appeal_planned
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
            validated_data['ifrc'] = dref.ifrc
            validated_data['icrc'] = dref.icrc
            validated_data['partner_national_society'] = dref.partner_national_society
            validated_data['government_requested_assistance'] = dref.government_requested_assistance
            validated_data['national_authorities'] = dref.national_authorities
            validated_data['un_or_other_actor'] = dref.un_or_other_actor
            validated_data['major_coordination_mechanism'] = dref.major_coordination_mechanism
            validated_data['people_assisted'] = dref.people_assisted
            validated_data['selection_criteria'] = dref.selection_criteria
            validated_data['entity_affected'] = dref.entity_affected
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
            validated_data['created_by'] = self.context['request'].user
            validated_data['new_operational_start_date'] = dref.date_of_approval
            validated_data['operational_update_number'] = 1  # if no any dref operational update created so far
            validated_data['dref_allocated_so_far'] = dref.amount_requested
            operational_update = super().create(validated_data)
            operational_update.planned_interventions.add(*dref.planned_interventions.all())
            operational_update.images.add(*dref.images.all())
            operational_update.national_society_actions.add(*dref.national_society_actions.all())
            operational_update.needs_identified.add(*dref.needs_identified.all())
            if DrefCountryDistrict.objects.filter(dref=dref).exists():
                dref_country_district = DrefCountryDistrict.objects.filter(dref=dref)
                for cd in dref_country_district:
                    country_district = DrefOperationalUpdateCountryDistrict.objects.create(
                        country=cd.country,
                        dref_operational_update=operational_update
                    )
                    country_district.district.add(*cd.district.all())
        else:
            # get the latest dref operational update
            operational_object = dref_operational_update.order_by('-operational_update_number')[0]
            validated_data['title'] = operational_object.title
            validated_data['national_society'] = operational_object.national_society
            validated_data['disaster_type'] = operational_object.disaster_type
            validated_data['type_of_onset'] = operational_object.type_of_onset
            validated_data['disaster_category'] = operational_object.disaster_category
            validated_data['number_of_people_targeted'] = operational_object.number_of_people_targeted
            validated_data['number_of_people_affected'] = operational_object.number_of_people_affected
            validated_data['emergency_appeal_planned'] = operational_object.emergency_appeal_planned
            validated_data['appeal_code'] = operational_object.appeal_code
            validated_data['glide_code'] = operational_object.glide_code
            validated_data['ifrc_appeal_manager_name'] = operational_object.ifrc_appeal_manager_name
            validated_data['ifrc_appeal_manager_email'] = operational_object.ifrc_appeal_manager_email
            validated_data['ifrc_appeal_manager_title'] = operational_object.ifrc_appeal_manager_title
            validated_data['ifrc_appeal_manager_phone_number'] = operational_object.ifrc_appeal_manager_phone_number
            validated_data['ifrc_project_manager_name'] = operational_object.ifrc_project_manager_name
            validated_data['ifrc_project_manager_email'] = operational_object.ifrc_project_manager_email
            validated_data['ifrc_project_manager_title'] = operational_object.ifrc_project_manager_title
            validated_data['ifrc_project_manager_phone_number'] = operational_object.ifrc_project_manager_phone_number
            validated_data['national_society_contact_name'] = operational_object.national_society_contact_name
            validated_data['national_society_contact_email'] = operational_object.national_society_contact_email
            validated_data['national_society_contact_title'] = operational_object.national_society_contact_title
            validated_data['national_society_contact_phone_number'] = operational_object.national_society_contact_phone_number
            validated_data['media_contact_name'] = operational_object.media_contact_name
            validated_data['media_contact_email'] = operational_object.media_contact_email
            validated_data['media_contact_title'] = operational_object.media_contact_title
            validated_data['media_contact_phone_number'] = operational_object.media_contact_phone_number
            validated_data['ifrc_emergency_name'] = operational_object.ifrc_emergency_name
            validated_data['ifrc_emergency_title'] = operational_object.ifrc_emergency_title
            validated_data['ifrc_emergency_phone_number'] = operational_object.ifrc_emergency_phone_number
            validated_data['ifrc_emergency_email'] = operational_object.ifrc_emergency_email
            validated_data['ifrc'] = operational_object.ifrc
            validated_data['icrc'] = operational_object.icrc
            validated_data['partner_national_society'] = operational_object.partner_national_society
            validated_data['government_requested_assistance'] = operational_object.government_requested_assistance
            validated_data['national_authorities'] = operational_object.national_authorities
            validated_data['un_or_other_actor'] = operational_object.un_or_other_actor
            validated_data['major_coordination_mechanism'] = operational_object.major_coordination_mechanism
            validated_data['people_assisted'] = operational_object.people_assisted
            validated_data['selection_criteria'] = operational_object.selection_criteria
            validated_data['entity_affected'] = operational_object.entity_affected
            validated_data['women'] = operational_object.women
            validated_data['men'] = operational_object.men
            validated_data['girls'] = operational_object.girls
            validated_data['boys'] = operational_object.boys
            validated_data['disability_people_per'] = operational_object.disability_people_per
            validated_data['people_per_urban'] = operational_object.people_per_urban
            validated_data['people_per_local'] = operational_object.people_per_local
            validated_data['people_targeted_with_early_actions'] = operational_object.people_targeted_with_early_actions
            validated_data['displaced_people'] = operational_object.displaced_people
            validated_data['operation_objective'] = operational_object.operation_objective
            validated_data['response_strategy'] = operational_object.response_strategy
            validated_data['created_by'] = self.context['request'].user
            validated_data['operational_update_number'] = operational_object.operational_update_number + 1
            validated_data['new_operational_start_date'] = operational_object.dref.date_of_approval
            validated_data['dref_allocated_so_far'] = operational_object.total_dref_allocation
            operational_update = super().create(validated_data)
            operational_update.planned_interventions.add(*operational_object.planned_interventions.all())
            operational_update.images.add(*operational_object.images.all())
            operational_update.national_society_actions.add(*operational_object.national_society_actions.all())
            operational_update.needs_identified.add(*operational_object.needs_identified.all())
            if DrefOperationalUpdateCountryDistrict.objects.filter(dref_operational_update=operational_object).exists():
                dref_country_district = DrefOperationalUpdateCountryDistrict.objects.filter(dref_operational_update=operational_object)
                for cd in dref_country_district:
                    country_district = DrefOperationalUpdateCountryDistrict.objects.create(
                        country=cd.country,
                        dref_operational_update=operational_update
                    )
                    country_district.district.add(*cd.district.all())
        return operational_update

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
