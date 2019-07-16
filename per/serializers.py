from rest_framework import serializers
from django.contrib.auth.models import User
from api.models import Region
from .models import (
    Draft, Form, FormData, NSPhase, WorkPlan, Overview, NiceDocument
)
from api.serializers import (
    RegoCountrySerializer, UserSerializer
)

class ListDraftSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Draft
        fields = ('country', 'code', 'user', 'data',)

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

class ListNiceDocSerializer(serializers.ModelSerializer):
    country = RegoCountrySerializer()
    class Meta:
        model = NiceDocument
        fields = ('name', 'country', 'document', 'document_url', 'visibility')

class ShortFormSerializer(serializers.ModelSerializer):
    country = RegoCountrySerializer()
    class Meta:
        model = Form
        fields = ('name', 'code', 'updated_at', 'country', 'language', 'id',)

class EngagedNSPercentageSerializer(serializers.ModelSerializer):
    country__count = serializers.IntegerField()
    forms_sent = serializers.IntegerField()
    class Meta:
        model = Region
        fields = ('id', 'country__count', 'forms_sent',)

class GlobalPreparednessSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField(max_length=10)
    question_id = serializers.CharField(max_length=20)
    class Meta:
        fields = ('id', 'code', 'question_id',)

class NSPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = NSPhase
        fields = ('id', 'country', 'phase', 'updated_at')

class MiniUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')

class WorkPlanSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer()
    class Meta:
        model = WorkPlan
        fields = '__all__'

class OverviewSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer()
    country = RegoCountrySerializer()
    class Meta:
        model = Overview
        fields = '__all__'
