from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Draft, Form, FormData,
)
from api.serializers import (
    RegoCountrySerializer, UserSerializer
)

class ListDraftSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Draft
        fields = ('code', 'user', 'data',)

class FormStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = ('name', 'code', 'country_id', 'language', 'id',)

class ListFormSerializer(serializers.ModelSerializer):
    country = RegoCountrySerializer()
    user = UserSerializer()
    class Meta:
        model = Form
        fields = ('name', 'code', 'updated_at', 'user', 'country', 'language', 'id',)

class ListFormDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormData
        fields = ('form', 'question_id', 'selected_option', 'notes')

class ShortFormSerializer(serializers.ModelSerializer):
    country = RegoCountrySerializer()
    class Meta:
        model = Form
        fields = ('name', 'code', 'updated_at', 'country', 'language', 'id',)
