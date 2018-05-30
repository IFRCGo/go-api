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

class ERUOwnerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ERUOwner
        fields = ('created_at', 'updated_at')
