from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Form,
)

class ListFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = ('name', 'updated_at', 'id',)
