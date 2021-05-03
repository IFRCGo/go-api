from django.utils.translation import ugettext
from rest_framework import serializers
from enumfields.drf.serializers import EnumSupportSerializerMixin

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

    OperationTypes,
    ProgrammeTypes,
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


class PersonnelDeploymentSerializer(ModelSerializer):
    country_deployed_to = MiniCountrySerializer()
    event_deployed_to = ListEventSerializer()

    class Meta:
        model = PersonnelDeployment
        fields = ('country_deployed_to', 'region_deployed_to', 'event_deployed_to', 'comments', 'id',)


class MolnixTagSerializer(ModelSerializer):

    class Meta:
        fields = ('id', 'molnix_id', 'name', 'color', 'tag_type')
        model = MolnixTag


class PersonnelDeploymentCsvSerializer(ModelSerializer):
    country_deployed_to = MicroCountrySerializer()
    event_deployed_to = ListEventForPersonnelCsvSerializer()

    class Meta:
        model = PersonnelDeployment
        fields = ('country_deployed_to', 'event_deployed_to', 'comments', 'id')


class PersonnelSerializer(ModelSerializer):
    country_from = MiniCountrySerializer()
    deployment = PersonnelDeploymentSerializer()
    molnix_tags = MolnixTagSerializer(many=True, read_only=True)

    class Meta:
        model = Personnel
        fields = ('start_date', 'end_date', 'name', 'role', 'type', 'country_from',
                  'deployment', 'molnix_id', 'molnix_tags', 'is_active', 'id',)


class PersonnelCsvSerializer(ModelSerializer):
    country_from = MicroCountrySerializer()
    deployment = PersonnelDeploymentCsvSerializer()

    class Meta:
        model = Personnel
        fields = ('start_date', 'end_date', 'name', 'role', 'type', 'country_from', 'deployment', 'id', 'is_active',)


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
    secondary_sectors_display = serializers.ListField(source='get_secondary_sectors_display', read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('user',)
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
