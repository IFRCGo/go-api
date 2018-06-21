from rest_framework import serializers
from .models import (
    ERUOwner,
    ERU,
    Heop,
    Fact,
    FactPerson,
    Rdrt,
    RdrtPerson,
    PartnerSocietyActivities,
    PartnerSocietyDeployment,
)
from api.serializers import (
    MiniEventSerializer,
    DisasterTypeSerializer,
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
    event = MiniEventSerializer()
    eru_owner = ERUOwnerSerializer()
    class Meta:
        model = ERU
        fields = ('type', 'units', 'equipment_units', 'deployed_to', 'event', 'eru_owner', 'available', 'id',)

class HeopSerializer(serializers.ModelSerializer):
    event = MiniEventSerializer()
    country = MiniCountrySerializer()
    class Meta:
        model = Heop
        fields = ('start_date', 'end_date', 'country', 'region', 'event', 'dtype', 'person', 'role', 'comments', 'id',)

class FactSerializer(serializers.ModelSerializer):
    event = MiniEventSerializer()
    country = MiniCountrySerializer()
    class Meta:
        model = Fact
        fields = ('start_date', 'country', 'region', 'event', 'dtype', 'comments', 'id',)

class RdrtSerializer(serializers.ModelSerializer):
    event = MiniEventSerializer()
    country = MiniCountrySerializer()
    class Meta:
        model = Rdrt
        fields = ('start_date', 'country', 'region', 'event', 'dtype', 'comments', 'id',)

class FactPersonSerializer(serializers.ModelSerializer):
    fact = FactSerializer()
    class Meta:
        model = FactPerson
        fields = ('start_date', 'end_date', 'name', 'role', 'society_deployed_from', 'fact', 'id',)

class RdrtPersonSerializer(serializers.ModelSerializer):
    rdrt = RdrtSerializer()
    class Meta:
        model = RdrtPerson
        fields = ('start_date', 'end_date', 'name', 'role', 'society_deployed_from', 'rdrt', 'id',)

class PartnerDeploymentActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerSocietyActivities
        fields = ('activity', 'id',)

class PartnerDeploymentSerializer(serializers.ModelSerializer):
    country_deployed_to = MiniCountrySerializer()
    district_deployed_to = MiniDistrictSerializer(many=True)
    activity = PartnerDeploymentActivitySerializer()
    class Meta:
        model = PartnerSocietyDeployment
        fields = ('start_date', 'end_date', 'name', 'role', 'parent_society', 'country_deployed_to', 'district_deployed_to', 'activity', 'id',)
