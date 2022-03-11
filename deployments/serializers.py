from django.utils.translation import ugettext
from django.contrib.auth.models import User

from rest_framework import serializers

from enumfields.drf.serializers import EnumSupportSerializerMixin

from main.utils import get_merged_items_by_fields
from main.writable_nested_serializers import (
    NestedCreateMixin,
    NestedUpdateMixin,
)
from lang.serializers import ModelSerializer
from api.serializers import (
    DisasterTypeSerializer,
    ListEventSerializer,
    ListEventForPersonnelCsvSerializer,
    MiniEventSerializer,
    MiniCountrySerializer,
    MicroCountrySerializer,
    MiniDistrictSerializer,
)

from .models import (
    ERUOwner,
    ERU,
    PersonnelDeployment,
    MolnixTag,
    Personnel,
    PartnerSocietyActivities,
    PartnerSocietyDeployment,
    RegionalProject,
    Project,
    EmergencyProject,
    EmergencyProjectActivitySector,
    EmergencyProjectActivityAction,
    EmergencyProjectActivityActionSupply,
    EmergencyProjectActivity,
    EmergencyProjectActivityLocation,

    OperationTypes,
    ProgrammeTypes,
)


class MiniUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name'
        )


class ERUSetSerializer(EnumSupportSerializerMixin, ModelSerializer):
    deployed_to = MiniCountrySerializer()
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = ERU
        fields = ('type', 'type_display', 'units', 'equipment_units', 'deployed_to', 'event', 'eru_owner', 'available', 'id',)


class ERUOwnerSerializer(ModelSerializer):
    eru_set = ERUSetSerializer(many=True)
    national_society_country = MiniCountrySerializer()

    class Meta:
        model = ERUOwner
        fields = ('created_at', 'updated_at', 'national_society_country', 'eru_set', 'id',)


class ERUSerializer(EnumSupportSerializerMixin, ModelSerializer):
    deployed_to = MiniCountrySerializer()
    event = ListEventSerializer()
    eru_owner = ERUOwnerSerializer()
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = ERU
        fields = ('type', 'type_display', 'units', 'equipment_units', 'deployed_to', 'event', 'eru_owner', 'available', 'id',)


class ERUOwnerMiniSerializer(ModelSerializer):
    national_society_country_details = MiniCountrySerializer(source='national_society_country', read_only=True)

    class Meta:
        model = ERUOwner
        fields = ('id', 'national_society_country_details',)


class ERUMiniSerializer(EnumSupportSerializerMixin, ModelSerializer):
    eru_owner_details = ERUOwnerMiniSerializer(source='eru_owner', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = ERU
        fields = (
            'id', 'type', 'type_display', 'units', 'equipment_units', 'eru_owner_details'
        )


class PersonnelDeploymentSerializer(ModelSerializer):
    country_deployed_to = MiniCountrySerializer()
    event_deployed_to = ListEventSerializer()

    class Meta:
        model = PersonnelDeployment
        fields = ('country_deployed_to', 'region_deployed_to', 'event_deployed_to', 'comments', 'id',)


class MolnixTagSerializer(ModelSerializer):

    class Meta:
        fields = ('id', 'molnix_id', 'name', 'description', 'color', 'tag_type')
        model = MolnixTag


class PersonnelDeploymentCsvSerializer(ModelSerializer):
    country_deployed_to = MicroCountrySerializer()
    event_deployed_to = ListEventForPersonnelCsvSerializer()

    class Meta:
        model = PersonnelDeployment
        fields = ('country_deployed_to', 'event_deployed_to', 'comments', 'id')


class PersonnelSerializer(ModelSerializer):
    country_from = MiniCountrySerializer()
    country_to = MiniCountrySerializer()
    deployment = PersonnelDeploymentSerializer()
    molnix_tags = MolnixTagSerializer(many=True, read_only=True)

    class Meta:
        model = Personnel
        fields = (
            'start_date', 'end_date', 'name', 'role', 'type', 'country_from', 'country_to',
            'deployment', 'molnix_id', 'molnix_tags', 'is_active', 'id',
        )


class PersonnelCsvSerializer(ModelSerializer):
    country_from = MicroCountrySerializer()
    country_to = MicroCountrySerializer()
    deployment = PersonnelDeploymentCsvSerializer()

    class Meta:
        model = Personnel
        fields = (
            'start_date', 'end_date', 'name', 'role', 'type', 'country_from', 'country_to', 'deployment', 'id', 'is_active',
        )


class PersonnelSerializerAnon(ModelSerializer):
    country_from = MiniCountrySerializer()
    country_to = MiniCountrySerializer()
    deployment = PersonnelDeploymentSerializer()
    molnix_tags = MolnixTagSerializer(many=True, read_only=True)

    class Meta:
        model = Personnel
        fields = (
            'start_date', 'end_date', 'role', 'type', 'country_from', 'country_to',
            'deployment', 'molnix_id', 'molnix_tags', 'is_active', 'id',
        )


class PersonnelCsvSerializerAnon(ModelSerializer):
    country_from = MicroCountrySerializer()
    country_to = MiniCountrySerializer()
    deployment = PersonnelDeploymentCsvSerializer()

    class Meta:
        model = Personnel
        fields = ('start_date', 'end_date', 'role', 'type', 'country_from', 'country_to', 'deployment', 'id', 'is_active',)


class PersonnelSerializerSuper(ModelSerializer):
    # Superusers can see molnix-status
    country_from = MiniCountrySerializer()
    country_to = MiniCountrySerializer()
    deployment = PersonnelDeploymentSerializer()
    molnix_tags = MolnixTagSerializer(many=True, read_only=True)

    class Meta:
        model = Personnel
        fields = ('start_date', 'end_date', 'name', 'role', 'type', 'country_from', 'country_to',
                  'deployment', 'molnix_id', 'molnix_tags', 'molnix_status', 'is_active', 'id',)


class PersonnelCsvSerializerSuper(ModelSerializer):
    # Superusers can see molnix-status
    country_from = MicroCountrySerializer()
    country_to = MicroCountrySerializer()
    deployment = PersonnelDeploymentCsvSerializer()

    class Meta:
        model = Personnel
        fields = ('start_date', 'end_date', 'name', 'role', 'type', 'country_from', 'country_to',
                  'deployment', 'molnix_id', 'molnix_status', 'is_active', 'id',)


class PartnerDeploymentActivitySerializer(ModelSerializer):

    class Meta:
        model = PartnerSocietyActivities
        fields = ('activity', 'id',)


class PartnerDeploymentTableauSerializer(serializers.ModelSerializer):
    parent_society = MiniCountrySerializer()
    country_deployed_to = MiniCountrySerializer()
    district_deployed_to = serializers.SerializerMethodField()
    activity = PartnerDeploymentActivitySerializer()

    def get_district_deployed_to(self, obj):
        district_fields = {
            'name': ''
        }
        district_deployed_to = obj.district_deployed_to.all()
        if len(district_deployed_to) > 0:
            district_fields['name'] = ', '.join([str(district.name) for district in district_deployed_to])
        return district_fields

    class Meta:
        model = PartnerSocietyDeployment
        fields = (
            'start_date', 'end_date', 'name', 'role', 'parent_society', 'country_deployed_to',
            'district_deployed_to', 'activity', 'id',
        )


class PartnerDeploymentSerializer(ModelSerializer):
    parent_society = MiniCountrySerializer()
    country_deployed_to = MiniCountrySerializer()
    district_deployed_to = MiniDistrictSerializer(many=True)
    activity = PartnerDeploymentActivitySerializer()

    class Meta:
        model = PartnerSocietyDeployment
        fields = (
            'start_date', 'end_date', 'name', 'role', 'parent_society', 'country_deployed_to',
            'district_deployed_to', 'activity', 'id',
        )


class RegionalProjectSerializer(ModelSerializer):
    class Meta:
        model = RegionalProject
        fields = '__all__'


class ProjectSerializer(EnumSupportSerializerMixin, ModelSerializer):
    project_country_detail = MiniCountrySerializer(source='project_country', read_only=True)
    project_districts_detail = MiniDistrictSerializer(source='project_districts', read_only=True, many=True)
    reporting_ns_detail = MiniCountrySerializer(source='reporting_ns', read_only=True)
    dtype_detail = DisasterTypeSerializer(source='dtype', read_only=True)
    regional_project_detail = RegionalProjectSerializer(source='regional_project', read_only=True)
    event_detail = MiniEventSerializer(source='event', read_only=True)
    primary_sector_display = serializers.CharField(source='get_primary_sector_display', read_only=True)
    programme_type_display = serializers.CharField(source='get_programme_type_display', read_only=True)
    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)
    secondary_sectors_display = serializers.ListField(source='get_secondary_sectors_display', read_only=True)
    modified_by_detail = MiniUserSerializer(source='modified_by', read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('user', 'modified_by')
        extra_kwargs = {
            field: {
                'allow_null': False, 'required': True,
            } for field in (
                'reporting_ns', 'name', 'project_country', 'programme_type', 'primary_sector', 'project_districts',
            )
        }

    def validate(self, data):
        d_project_districts = data['project_districts']
        # Override country with district's country
        if isinstance(d_project_districts, list) and len(d_project_districts):
            data['project_country'] = data['project_districts'][0].country
            for project in data['project_districts'][1:]:
                if project.country != data['project_country']:
                    raise serializers.ValidationError(ugettext('Different country found for given districts'))
        if (
            data['operation_type'] == OperationTypes.EMERGENCY_OPERATION and
            data['programme_type'] == ProgrammeTypes.MULTILATERAL and
            data.get('event') is None
        ):
            raise serializers.ValidationError(
                ugettext('Event should be provided if operation type is Emergency Operation and programme type is Multilateral')
            )
        return data

    def create(self, validated_data):
        project = super().create(validated_data)
        project.user = self.context['request'].user
        project.save()
        return project

    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ProjectCsvSerializer(ProjectSerializer):
    secondary_sectors = serializers.SerializerMethodField()
    secondary_sectors_display = serializers.SerializerMethodField()
    project_districts_detail = serializers.SerializerMethodField()

    class Meta:
        model = Project
        exclude = ['project_districts']

    def get_secondary_sectors(self, obj):
        return ', '.join([str(sector.value) for sector in obj.secondary_sectors])

    def get_secondary_sectors_display(self, obj):
        return ', '.join(obj.get_secondary_sectors_display())

    def get_project_districts_detail(self, obj):
        return get_merged_items_by_fields(
            obj.project_districts.all(),
            ['name', 'code', 'id', 'is_enclave', 'is_deprecated']
        )


class CharKeyValueSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField()

    @staticmethod
    def choices_to_data(choices):
        return [
            {
                'key': key,
                'value': value,
            }
            for key, value in choices
        ]


# ------ Emergency Project -- [Start]
class EmergencyProjectActivitySectorSerializer(ModelSerializer):
    class Meta:
        model = EmergencyProjectActivitySector
        fields = ('id', 'title', 'order',)


class EmergencyProjectActivityActionSupplySerializer(ModelSerializer):
    class Meta:
        model = EmergencyProjectActivityActionSupply
        fields = ('id', 'title', 'order',)


class EmergencyProjectActivityActionSerializer(ModelSerializer):
    supplies_details = EmergencyProjectActivityActionSupplySerializer(
        source='supplies',
        read_only=True,
        many=True,
    )

    class Meta:
        model = EmergencyProjectActivityAction
        fields = ('id', 'sector', 'title', 'order', 'supplies_details',)


class EmergencyProjectActivityLocationSerializer(ModelSerializer):
    class Meta:
        model = EmergencyProjectActivityLocation
        fields = '__all__'


class EmergencyProjectOptionsSerializer(serializers.Serializer):
    sectors = EmergencyProjectActivitySectorSerializer(read_only=True, many=True)
    actions = EmergencyProjectActivityActionSerializer(read_only=True, many=True)
    activity_leads = CharKeyValueSerializer(read_only=True, many=True)
    activity_status = CharKeyValueSerializer(read_only=True, many=True)


class EmergencyProjectActivitySerializer(
    NestedUpdateMixin,
    NestedCreateMixin,
    ModelSerializer
):
    supplies = serializers.DictField(child=serializers.IntegerField(), required=False)
    custom_supplies = serializers.DictField(child=serializers.IntegerField(),)
    points = EmergencyProjectActivityLocationSerializer(many=True, required=False)
    sector_details = EmergencyProjectActivitySectorSerializer(source='sector', read_only=True)
    action_details = EmergencyProjectActivityActionSerializer(source='action', read_only=True)

    class Meta:
        model = EmergencyProjectActivity
        exclude = ('project',)

    def validate(self, data):
        sector = data.get('sector', self.instance and self.instance.sector)
        action = data.get('action', self.instance and self.instance.action)
        supplies = data.get('supplies')
        if action:
            data['sector'] = sector = action.sector
        if sector is None:
            raise serializers.ValidationError({
                'sector': ugettext('This is required, Or provide a valid action.')
            })
        if supplies:
            supplies_keys = supplies.keys()
            action_supplies_id = list(action.supplies.values_list('id', flat=True))
            if invalid_keys := [key for key in supplies_keys if int(key) not in action_supplies_id]:
                raise serializers.ValidationError({
                    'supplies': ugettext(
                        'Invalid supplies keys: %s' % ', '.join(invalid_keys)
                    ),
                })
        return data


class EmergencyProjectSerializer(
    EnumSupportSerializerMixin,
    NestedUpdateMixin,
    NestedCreateMixin,
    ModelSerializer,
):
    created_by_details = MiniUserSerializer(source='created_by', read_only=True)
    modified_by_details = MiniUserSerializer(source='modified_by', read_only=True)
    event_details = MiniEventSerializer(source='event', read_only=True)
    reporting_ns_details = MiniCountrySerializer(source='reporting_ns', read_only=True)
    deployed_eru_details = ERUMiniSerializer(source='deployed_eru', read_only=True)
    districts_details = MiniDistrictSerializer(source='districts', read_only=True, many=True)
    activities = EmergencyProjectActivitySerializer(many=True, required=False)
    # Enums
    activity_lead_display = serializers.CharField(source='get_activity_lead_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    country_details = MiniCountrySerializer(source='country', read_only=True)

    class Meta:
        model = EmergencyProject
        fields = '__all__'
        read_only_fields = (
            'created_by',
            'created_at',
            'modified_by',
            'modified_at',
        )

    def validate(self, data):
        event = data.get('event', self.instance and self.instance.event)
        countries_id = list(event.countries.values_list('id', flat=True))
        reporting_ns = data.get('reporting_ns', self.instance and self.instance.reporting_ns)
        deployed_eru = data.get('deployed_eru', self.instance and self.instance.deployed_eru)
        country = data.get('country', None)
        if country and country.id not in countries_id:
            raise serializers.ValidationError({
                'country': ugettext("Country should be from event's countries"),
            })
        for district in data.get('districts') or []:
            if district.country_id != country.id:
                raise serializers.ValidationError({
                    'districts': ugettext("All region/province should be from selected country"),
                })
        if data['activity_lead'] == EmergencyProject.ActivityLead.NATIONAL_SOCIETY:
            if reporting_ns is None:
                raise serializers.ValidationError({
                    'reporting_ns': ugettext('Reporting NS is required when National Society is leading the activity'),
                })
        else:
            if deployed_eru is None:
                raise serializers.ValidationError({
                    'deployed_eru': ugettext('Deployed ERU is required when Deployed ERU is leading the activity'),
                })
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['modified_by'] = self.context['request'].user
        return super().update(instance, validated_data)

# ------ Emergency Project -- [End]
