from rest_framework import serializers

from .models import (
    Language,
    String,
)


class StringSerializer(serializers.ModelSerializer):
    action = serializers.CharField(write_only=True)

    class Meta:
        model = String
        fields = '__all__'


class ListLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class LanguageSerializer(ListLanguageSerializer):
    strings = StringSerializer(source='string_set', many=True, read_only=True)


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


class LanguageBulkActionsSerializer(serializers.Serializer):
    actions = LanguageBulkActionSerializer(many=True)
