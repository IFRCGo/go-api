from rest_framework import serializers

from .models import (
    String,
)


class StringSerializer(serializers.ModelSerializer):
    class Meta:
        model = String
        fields = '__all__'


class LanguageBulkActionSerializer(serializers.Serializer):
    SET = 'set'
    DELETE = 'delete'

    ACTION_CHOICES = (
        (SET, 'Set'),
        (DELETE, 'Delete'),
    )

    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    key = serializers.CharField()
    value = serializers.CharField(required=False)
    hash = serializers.CharField(max_length=32, required=False)


class LanguageBulkActionsSerializer(serializers.Serializer):
    actions = LanguageBulkActionSerializer(many=True)
