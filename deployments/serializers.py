from rest_framework import serializers
from .models import (
    ERUOwner,
    ERU,
    Heop,
    Fact,
    FactPerson,
    Rdrt,
    RdrtPerson,
)
from api.serializers import (
    MiniEventSerializer,
    DisasterTypeSerializer,
)

class ERUOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ERUOwner
        fields = ('created_at', 'updated_at', 'national_society_country', 'id',)

class ERUSerializer(serializers.ModelSerializer):
    event = MiniEventSerializer()
    eru_owner = ERUOwnerSerializer()
    class Meta:
        model = ERU
        fields = ('type', 'units', 'equipment_units', 'deployed_to', 'event', 'eru_owner', 'available', 'id',)

class HeopSerializer(serializers.ModelSerializer):
    event = MiniEventSerializer()
    class Meta:
        model = Heop
        fields = ('start_date', 'end_date', 'country', 'region', 'event', 'dtype', 'person', 'role', 'comments', 'id',)

class FactSerializer(serializers.ModelSerializer):
    event = MiniEventSerializer()
    class Meta:
        model = Fact
        fields = ('start_date', 'country', 'region', 'event', 'dtype', 'comments', 'id',)

class RdrtSerializer(serializers.ModelSerializer):
    event = MiniEventSerializer()
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
