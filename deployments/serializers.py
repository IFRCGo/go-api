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
    DisasterTypeSerializer
)

class ERUOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ERUOwner
        fields = ('created_at', 'updated_at', 'national_society_country')

class ERUSerializer(serializers.ModelSerializer):
    class Meta:
        model = ERU
        fields = ('type', 'units', 'equipment_units', 'deployed_to', 'event', 'eru_owner', 'available')

class HeopSerializer(serializers.ModelSerializer):
    dtype = DisasterTypeSerializer()
    class Meta:
        model = Heop
        fields = ('start_date', 'end_date', 'country', 'region', 'event', 'dtype', 'person', 'role', 'comments')

class FactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fact
        fields = ('start_date', 'country', 'region', 'event', 'dtype', 'comments')

class RdrtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rdrt
        fields = ('start_date', 'country', 'region', 'event', 'dtype', 'comments')

class FactPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactPerson
        fields = ('start_date', 'end_date', 'name', 'role', 'society_deployed_from', 'fact')

class RdrtPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = RdrtPerson
        fields = ('start_date', 'end_date', 'name', 'role', 'society_deployed_from', 'rdrt')
