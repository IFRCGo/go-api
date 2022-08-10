import os
import datetime

from django.utils.translation import ugettext
from django.db import models

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
    MiniCountrySerializer
)

from dref.models import (
    Dref,
    PlannedIntervention,
    PlannedInterventionIndicators,
    NationalSocietyAction,
    IdentifiedNeed,
    RiskSecurity,
    DrefFile,
    DrefOperationalUpdate,
    DrefFinalReport,
)


class RiskSecuritySerializer(ModelSerializer):
    class Meta:
        model = RiskSecurity
        fields = '__all__'


class PlannedInterventionIndicatorsSerializer(ModelSerializer):
    class Meta:
        model = PlannedInterventionIndicators
        fields = '__all__'


class DrefFileSerializer(ModelSerializer):
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    file = serializers.FileField(required=False)

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


class MiniOperationalUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrefOperationalUpdate
        fields = [
            'id',
            'title',
            'is_published',
            'operational_update_number',
        ]


class MiniDrefFinalReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrefFinalReport
        fields = [
            'id',
            'title',
            'is_published',
        ]


class DrefSerializer(
    EnumSupportSerializerMixin,
    NestedUpdateMixin,
    NestedCreateMixin,
    ModelSerializer
):
    MAX_NUMBER_OF_IMAGES = 2
    ALLOWED_BUDGET_FILE_EXTENSIONS = ["pdf"]
    ALLOWED_ASSESSMENT_REPORT_EXTENSIONS = ["pdf", "docx", "pptx"]
    MAX_OPERATION_TIMEFRAME = 30
    national_society_actions = NationalSocietyActionSerializer(many=True, required=False)
    needs_identified = IdentifiedNeedSerializer(many=True, required=False)
    planned_interventions = PlannedInterventionSerializer(many=True, required=False)
    type_of_onset_display = serializers.CharField(source='get_type_of_onset_display', read_only=True)
    disaster_category_display = serializers.CharField(source='get_disaster_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    modified_by_details = UserNameSerializer(source='modified_by', read_only=True)
    event_map_file = DrefFileSerializer(source='event_map', required=False, allow_null=True)
    images_file = DrefFileSerializer(many=True, required=False, allow_null=True, source='images')
    # field_report_details = MiniFieldReportSerializer(source='field_report', read_only=True)
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    users_details = UserNameSerializer(source='users', many=True, read_only=True)
    budget_file_file = DrefFileSerializer(source='budget_file', required=False, allow_null=True)
    cover_image_file = DrefFileSerializer(source='cover_image', required=False, allow_null=True)
    disaster_type_details = DisasterTypeSerializer(source='disaster_type', read_only=True)
    operational_update_details = MiniOperationalUpdateSerializer(source='drefoperationalupdate_set', many=True, read_only=True)
    dref_final_report_details = MiniDrefFinalReportSerializer(source='dreffinalreport', read_only=True)
    country_details = MiniCountrySerializer(source='country', read_only=True)
    district_details = MiniDistrictSerializer(source='district', read_only=True, many=True)
    assessment_report_details = DrefFileSerializer(source='assessment_report', read_only=True)
    suporting_document_details = DrefFileSerializer(read_only=True, source='suporting_docuement')
    risk_security = RiskSecuritySerializer(many=True, required=False)

    class Meta:
        model = Dref
        read_only_fields = ('modified_by', 'created_by', 'budget_file_preview')
        exclude = ('cover_image', 'event_map', 'images')

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
        if self.instance and DrefFinalReport.objects.filter(dref=self.instance, is_published=True).exists():
            raise serializers.ValidationError(
                ugettext('Can\'t Update %s dref for publish Field Report' % self.instance.id)
            )
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

    def validate_assessment_report(self, assessment_report):
        if assessment_report is None:
            return
        extension = os.path.splitext(assessment_report.file.name)[1].replace(".", "")
        if extension.lower() not in self.ALLOWED_ASSESSMENT_REPORT_EXTENSIONS:
            raise serializers.ValidationError(
                f'Invalid uploaded file extension: {extension}, Supported only {self.ALLOWED_ASSESSmentREPORT_EXTENSIONS} Files'
            )
        return assessment_report

    def validate_operation_timeframe(self, operation_timeframe):
        if operation_timeframe and operation_timeframe > self.MAX_OPERATION_TIMEFRAME:
            raise serializers.ValidationError(
                ugettext('Operation timeframe can\'t be greater than %s', self.MAX_OPERATION_TIMEFRAME)
            )

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
    photos_details = DrefFileSerializer(source='photos', many=True, read_only=True)
    modified_by_details = UserNameSerializer(source='modified_by', read_only=True)
    disaster_type_details = DisasterTypeSerializer(source='disaster_type', read_only=True)
    budget_file_details = DrefFileSerializer(source='budget_file', read_only=True)
    cover_image_details = DrefFileSerializer(source='cover_image', read_only=True)
    country_details = MiniCountrySerializer(source='country', read_only=True)
    district_details = MiniDistrictSerializer(source='district', read_only=True, many=True)
    assessment_report_details = DrefFileSerializer(source='assessment_report', read_only=True)

    class Meta:
        model = DrefOperationalUpdate
        fields = '__all__'
        read_only_fields = ('operational_update_number', )

    def validate(self, data):
        dref = data.get('dref')
        if not self.instance and dref:
            if not dref.is_published:
                raise serializers.ValidationError(
                    ugettext('Can\'t create Operational Update for not published %s dref.' % dref.id)
                )
            # get the latest dref_operation_update and check whether it is published or not, exclude no operational object created so far
            dref_operational_update = DrefOperationalUpdate.objects.filter(dref=dref).order_by('-operational_update_number').first()
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
        dref = validated_data['dref']
        dref_operational_update = DrefOperationalUpdate.objects.filter(dref=dref).order_by('-operational_update_number').first()
        if not dref_operational_update:
            validated_data['title'] = dref.title
            validated_data['title_prefix'] = dref.title_prefix
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
            validated_data['event_description'] = dref.event_description
            validated_data['anticipatory_actions'] = dref.anticipatory_actions
            validated_data['event_scope'] = dref.event_scope
            validated_data['cover_image'] = dref.cover_image
            validated_data['budget_file'] = dref.budget_file
            validated_data['assessment_report'] = dref.assessment_report
            validated_data['country'] = dref.country
            operational_update = super().create(validated_data)
            operational_update.planned_interventions.add(*dref.planned_interventions.all())
            operational_update.images.add(*dref.images.all())
            operational_update.national_society_actions.add(*dref.national_society_actions.all())
            operational_update.needs_identified.add(*dref.needs_identified.all())
            operational_update.district.add(*dref.district.all())
        else:
            # get the latest dref operational update
            validated_data['title'] = dref_operational_update.title
            validated_data['title_prefix'] = dref_operational_update.title_prefix
            validated_data['national_society'] = dref_operational_update.national_society
            validated_data['disaster_type'] = dref_operational_update.disaster_type
            validated_data['type_of_onset'] = dref_operational_update.type_of_onset
            validated_data['disaster_category'] = dref_operational_update.disaster_category
            validated_data['number_of_people_targeted'] = dref_operational_update.number_of_people_targeted
            validated_data['number_of_people_affected'] = dref_operational_update.number_of_people_affected
            validated_data['emergency_appeal_planned'] = dref_operational_update.emergency_appeal_planned
            validated_data['appeal_code'] = dref_operational_update.appeal_code
            validated_data['glide_code'] = dref_operational_update.glide_code
            validated_data['ifrc_appeal_manager_name'] = dref_operational_update.ifrc_appeal_manager_name
            validated_data['ifrc_appeal_manager_email'] = dref_operational_update.ifrc_appeal_manager_email
            validated_data['ifrc_appeal_manager_title'] = dref_operational_update.ifrc_appeal_manager_title
            validated_data['ifrc_appeal_manager_phone_number'] = dref_operational_update.ifrc_appeal_manager_phone_number
            validated_data['ifrc_project_manager_name'] = dref_operational_update.ifrc_project_manager_name
            validated_data['ifrc_project_manager_email'] = dref_operational_update.ifrc_project_manager_email
            validated_data['ifrc_project_manager_title'] = dref_operational_update.ifrc_project_manager_title
            validated_data['ifrc_project_manager_phone_number'] = dref_operational_update.ifrc_project_manager_phone_number
            validated_data['national_society_contact_name'] = dref_operational_update.national_society_contact_name
            validated_data['national_society_contact_email'] = dref_operational_update.national_society_contact_email
            validated_data['national_society_contact_title'] = dref_operational_update.national_society_contact_title
            validated_data['national_society_contact_phone_number'] = dref_operational_update.national_society_contact_phone_number
            validated_data['media_contact_name'] = dref_operational_update.media_contact_name
            validated_data['media_contact_email'] = dref_operational_update.media_contact_email
            validated_data['media_contact_title'] = dref_operational_update.media_contact_title
            validated_data['media_contact_phone_number'] = dref_operational_update.media_contact_phone_number
            validated_data['ifrc_emergency_name'] = dref_operational_update.ifrc_emergency_name
            validated_data['ifrc_emergency_title'] = dref_operational_update.ifrc_emergency_title
            validated_data['ifrc_emergency_phone_number'] = dref_operational_update.ifrc_emergency_phone_number
            validated_data['ifrc_emergency_email'] = dref_operational_update.ifrc_emergency_email
            validated_data['ifrc'] = dref_operational_update.ifrc
            validated_data['icrc'] = dref_operational_update.icrc
            validated_data['partner_national_society'] = dref_operational_update.partner_national_society
            validated_data['government_requested_assistance'] = dref_operational_update.government_requested_assistance
            validated_data['national_authorities'] = dref_operational_update.national_authorities
            validated_data['un_or_other_actor'] = dref_operational_update.un_or_other_actor
            validated_data['major_coordination_mechanism'] = dref_operational_update.major_coordination_mechanism
            validated_data['people_assisted'] = dref_operational_update.people_assisted
            validated_data['selection_criteria'] = dref_operational_update.selection_criteria
            validated_data['entity_affected'] = dref_operational_update.entity_affected
            validated_data['women'] = dref_operational_update.women
            validated_data['men'] = dref_operational_update.men
            validated_data['girls'] = dref_operational_update.girls
            validated_data['boys'] = dref_operational_update.boys
            validated_data['disability_people_per'] = dref_operational_update.disability_people_per
            validated_data['people_per_urban'] = dref_operational_update.people_per_urban
            validated_data['people_per_local'] = dref_operational_update.people_per_local
            validated_data['people_targeted_with_early_actions'] = dref_operational_update.people_targeted_with_early_actions
            validated_data['displaced_people'] = dref_operational_update.displaced_people
            validated_data['operation_objective'] = dref_operational_update.operation_objective
            validated_data['response_strategy'] = dref_operational_update.response_strategy
            validated_data['created_by'] = self.context['request'].user
            validated_data['operational_update_number'] = dref_operational_update.operational_update_number + 1
            validated_data['new_operational_start_date'] = dref_operational_update.dref.date_of_approval
            validated_data['dref_allocated_so_far'] = dref_operational_update.total_dref_allocation
            validated_data['event_description'] = dref_operational_update.event_description
            validated_data['anticipatory_actions'] = dref_operational_update.anticipatory_actions
            validated_data['event_scope'] = dref_operational_update.event_scope
            validated_data['cover_image'] = dref_operational_update.cover_image
            validated_data['budget_file'] = dref_operational_update.budget_file
            validated_data['assessment_report'] = dref_operational_update.assessment_report
            validated_data['country'] = dref_operational_update.country
            operational_update = super().create(validated_data)
            operational_update.planned_interventions.add(*dref_operational_update.planned_interventions.all())
            operational_update.images.add(*dref_operational_update.images.all())
            operational_update.national_society_actions.add(*dref_operational_update.national_society_actions.all())
            operational_update.needs_identified.add(*dref_operational_update.needs_identified.all())
            operational_update.district.add(*dref_operational_update.district.all())
        return operational_update

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class DrefFinalReportSerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    serializers.ModelSerializer
):
    MAX_NUMBER_OF_PHOTOS = 2
    national_society_actions = NationalSocietyActionSerializer(many=True, required=False)
    needs_identified = IdentifiedNeedSerializer(many=True, required=False)
    planned_interventions = PlannedInterventionSerializer(many=True, required=False)
    type_of_onset_display = serializers.CharField(source='get_type_of_onset_display', read_only=True)
    disaster_category_display = serializers.CharField(source='get_disaster_category_display', read_only=True)
    created_by_details = UserNameSerializer(source='created_by', read_only=True)
    event_map_details = DrefFileSerializer(source='event_map', read_only=True)
    photos_details = DrefFileSerializer(source='photos', many=True, read_only=True)
    country_details = MiniCountrySerializer(source='country', read_only=True)
    district_details = MiniDistrictSerializer(source='district', read_only=True, many=True)
    assessment_report_details = DrefFileSerializer(source='assessment_report', read_only=True)

    class Meta:
        model = DrefFinalReport
        fields = '__all__'

    def validate(self, data):
        dref = data.get('dref')
        # check if dref is published and operational_update associated with it is also published
        if not self.instance and dref:
            if not dref.is_published:
                raise serializers.ValidationError(
                    ugettext('Can\'t create Final Report for not published dref %s.' % dref.id)
                )
            dref_operational_update = DrefOperationalUpdate.objects.filter(
                dref=dref,
                is_published=False,
            ).values_list('id', flat=True)
            if dref_operational_update:
                raise serializers.ValidationError(
                    ugettext(
                        'Can\'t create Final Report for not published Operational Update %s ids ' % ','.join(map(str, dref_operational_update))
                    )
                )
        if self.instance and self.instance.is_published:
            raise serializers.ValidationError(
                ugettext(
                    'Can\'t update published final report %s.' % self.instance.id
                )
            )
        return data

    def validate_photos(self, photos):
        if photos and len(photos) > self.MAX_NUMBER_OF_PHOTOS:
            raise serializers.ValidationError('Can add utmost %s photos' % self.MAX_NUMBER_OF_PHOTOS)
        return photos

    def create(self, validated_data):
        # here check if there is operational update for corresponding dref
        # if yes copy from the latest operational update
        # else copy from dref
        dref = validated_data['dref']
        dref_operational_update = DrefOperationalUpdate.objects.filter(
            dref=dref,
        ).order_by('-operational_update_number').first()
        if dref_operational_update:
            validated_data['title'] = dref_operational_update.title
            validated_data['title_prefix'] = dref_operational_update.title_prefix
            validated_data['national_society'] = dref_operational_update.national_society
            validated_data['disaster_type'] = dref_operational_update.disaster_type
            validated_data['type_of_onset'] = dref_operational_update.type_of_onset
            validated_data['disaster_category'] = dref_operational_update.disaster_category
            validated_data['number_of_people_targeted'] = dref_operational_update.number_of_people_targeted
            validated_data['number_of_people_affected'] = dref_operational_update.number_of_people_affected
            validated_data['total_dref_allocation'] = dref_operational_update.total_dref_allocation
            validated_data['total_operation_timeframe'] = dref_operational_update.total_operation_timeframe
            validated_data['operation_start_date'] = dref_operational_update.dref.date_of_approval
            validated_data['appeal_code'] = dref_operational_update.appeal_code
            validated_data['glide_code'] = dref_operational_update.glide_code
            validated_data['ifrc_appeal_manager_name'] = dref_operational_update.ifrc_appeal_manager_name
            validated_data['ifrc_appeal_manager_email'] = dref_operational_update.ifrc_appeal_manager_email
            validated_data['ifrc_appeal_manager_title'] = dref_operational_update.ifrc_appeal_manager_title
            validated_data['ifrc_appeal_manager_phone_number'] = dref_operational_update.ifrc_appeal_manager_phone_number
            validated_data['ifrc_project_manager_name'] = dref_operational_update.ifrc_project_manager_name
            validated_data['ifrc_project_manager_email'] = dref_operational_update.ifrc_project_manager_email
            validated_data['ifrc_project_manager_title'] = dref_operational_update.ifrc_project_manager_title
            validated_data['ifrc_project_manager_phone_number'] = dref_operational_update.ifrc_project_manager_phone_number
            validated_data['national_society_contact_name'] = dref_operational_update.national_society_contact_name
            validated_data['national_society_contact_email'] = dref_operational_update.national_society_contact_email
            validated_data['national_society_contact_title'] = dref_operational_update.national_society_contact_title
            validated_data['national_society_contact_phone_number'] = dref_operational_update.national_society_contact_phone_number
            validated_data['media_contact_name'] = dref_operational_update.media_contact_name
            validated_data['media_contact_email'] = dref_operational_update.media_contact_email
            validated_data['media_contact_title'] = dref_operational_update.media_contact_title
            validated_data['media_contact_phone_number'] = dref_operational_update.media_contact_phone_number
            validated_data['ifrc_emergency_name'] = dref_operational_update.ifrc_emergency_name
            validated_data['ifrc_emergency_title'] = dref_operational_update.ifrc_emergency_title
            validated_data['ifrc_emergency_phone_number'] = dref_operational_update.ifrc_emergency_phone_number
            validated_data['ifrc_emergency_email'] = dref_operational_update.ifrc_emergency_email
            validated_data['ifrc'] = dref_operational_update.ifrc
            validated_data['icrc'] = dref_operational_update.icrc
            validated_data['partner_national_society'] = dref_operational_update.partner_national_society
            validated_data['government_requested_assistance'] = dref_operational_update.government_requested_assistance
            validated_data['national_authorities'] = dref_operational_update.national_authorities
            validated_data['un_or_other_actor'] = dref_operational_update.un_or_other_actor
            validated_data['major_coordination_mechanism'] = dref_operational_update.major_coordination_mechanism
            validated_data['people_assisted'] = dref_operational_update.people_assisted
            validated_data['selection_criteria'] = dref_operational_update.selection_criteria
            validated_data['entity_affected'] = dref_operational_update.entity_affected
            validated_data['women'] = dref_operational_update.women
            validated_data['men'] = dref_operational_update.men
            validated_data['girls'] = dref_operational_update.girls
            validated_data['boys'] = dref_operational_update.boys
            validated_data['disability_people_per'] = dref_operational_update.disability_people_per
            validated_data['people_per_urban'] = dref_operational_update.people_per_urban
            validated_data['people_per_local'] = dref_operational_update.people_per_local
            validated_data['people_targeted_with_early_actions'] = dref_operational_update.people_targeted_with_early_actions
            validated_data['displaced_people'] = dref_operational_update.displaced_people
            validated_data['operation_objective'] = dref_operational_update.operation_objective
            validated_data['response_strategy'] = dref_operational_update.response_strategy
            validated_data['created_by'] = self.context['request'].user
            validated_data['operation_start_date'] = dref_operational_update.dref.date_of_approval
            validated_data['event_description'] = dref_operational_update.event_description
            validated_data['anticipatory_actions'] = dref_operational_update.anticipatory_actions
            validated_data['event_scope'] = dref_operational_update.event_scope
            validated_data['event_map'] = dref_operational_update.dref.event_map
            validated_data['assessment_report'] = dref_operational_update.assessment_report
            validated_data['country'] = dref_operational_update.country
            dref_final_report = super().create(validated_data)
            dref_final_report.planned_interventions.add(*dref_operational_update.planned_interventions.all())
            dref_final_report.needs_identified.add(*dref_operational_update.needs_identified.all())
            dref_final_report.district.add(*dref_operational_update.district.all())
        else:
            validated_data['title'] = dref.title
            validated_data['title_prefix'] = dref.title_prefix
            validated_data['national_society'] = dref.national_society
            validated_data['disaster_type'] = dref.disaster_type
            validated_data['type_of_onset'] = dref.type_of_onset
            validated_data['disaster_category'] = dref.disaster_category
            validated_data['number_of_people_targeted'] = dref.num_assisted
            validated_data['number_of_people_affected'] = dref.num_affected
            validated_data['total_operation_timeframe'] = dref.operation_timeframe
            validated_data['operation_start_date'] = dref.date_of_approval
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
            validated_data['event_description'] = dref.event_description
            validated_data['anticipatory_actions'] = dref.anticipatory_actions
            validated_data['event_scope'] = dref.event_scope
            validated_data['event_map'] = dref.event_map
            validated_data['assessment_report'] = dref.assessment_report
            validated_data['country'] = dref.country
            dref_final_report = super().create(validated_data)
            dref_final_report.planned_interventions.add(*dref.planned_interventions.all())
            dref_final_report.needs_identified.add(*dref.needs_identified.all())
            dref_final_report.district.add(*dref.district.all())
            # also update is_final_report_created for dref
            dref.is_final_report_created = True
            dref.save(update_fields=['is_final_report_created'])
        return dref_final_report

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
