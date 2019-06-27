from rest_framework import serializers
from .models import (
    ERUOwner,
    ERU,
    PersonnelDeployment,
    Personnel,
    Heop,
    Fact,
    FactPerson,
    Rdrt,
    RdrtPerson,
    PartnerSocietyActivities,
    PartnerSocietyDeployment,
    Project
)
from api.serializers import (
    ListEventSerializer,
    MiniCountrySerializer,
    MiniDistrictSerializer,
)

class ERUSetSerializer(serializers.ModelSerializer):
    deployed_to = MiniCountrySerializer()
    class Meta:
        model = ERU
        fields = ('type', 'units', 'equipment_units', 'deployed_to', 'event', 'eru_owner', 'available', 'id',)

class ERUOwnerSerializer(serializers.ModelSerializer):
    eru_set = ERUSetSerializer(many=True)
    national_society_country = MiniCountrySerializer()
    class Meta:
        model = ERUOwner
        fields = ('created_at', 'updated_at', 'national_society_country', 'eru_set', 'id',)

class ERUSerializer(serializers.ModelSerializer):
    deployed_to = MiniCountrySerializer()
    event = ListEventSerializer()
    eru_owner = ERUOwnerSerializer()
    class Meta:
        model = ERU
        fields = ('type', 'units', 'equipment_units', 'deployed_to', 'event', 'eru_owner', 'available', 'id',)

class PersonnelDeploymentSerializer(serializers.ModelSerializer):
    country_deployed_to = MiniCountrySerializer()
    event_deployed_to = ListEventSerializer()
    class Meta:
        model = PersonnelDeployment
        fields = ('country_deployed_to', 'region_deployed_to', 'event_deployed_to', 'comments', 'id',)

class PersonnelSerializer(serializers.ModelSerializer):
    country_from = MiniCountrySerializer()
    deployment = PersonnelDeploymentSerializer()
    class Meta:
        model = Personnel
        fields = ('start_date', 'end_date', 'name', 'role', 'type', 'country_from', 'deployment', 'id',)

class PartnerDeploymentActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerSocietyActivities
        fields = ('activity', 'id',)

class PartnerDeploymentSerializer(serializers.ModelSerializer):
    parent_society = MiniCountrySerializer()
    country_deployed_to = MiniCountrySerializer()
    district_deployed_to = MiniDistrictSerializer(many=True)
    activity = PartnerDeploymentActivitySerializer()
    class Meta:
        model = PartnerSocietyDeployment
        fields = ('start_date', 'end_date', 'name', 'role', 'parent_society', 'country_deployed_to', 'district_deployed_to', 'activity', 'id',)

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'