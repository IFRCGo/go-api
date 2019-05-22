from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Form, FormData,
)

class ListFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = ('name', 'code', 'updated_at', 'user_id', 'country_id', 'ns', 'language', 'id',)

class ListFormDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormData
        fields = ('form', 'question_id', 'selected_option', 'notes')
