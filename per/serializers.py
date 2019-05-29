from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Form, FormData,
)
from api.serializers import (
    RegoCountrySerializer
)

class ListFormSerializer(serializers.ModelSerializer):
    country = RegoCountrySerializer()
    class Meta:
        model = Form
        fields = ('name', 'code', 'updated_at', 'user_id', 'country', 'language', 'id',)

class ListFormDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormData
        fields = ('form', 'question_id', 'selected_option', 'notes')
