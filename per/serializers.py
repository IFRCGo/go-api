from rest_framework import serializers
from django.contrib.auth.models import User
from enumfields.drf.serializers import EnumSupportSerializerMixin

from api.models import Region
from api.serializers import (
    RegoCountrySerializer, UserSerializer
)
from .models import (
    Form, FormData, NSPhase, WorkPlan, Overview, NiceDocument
)


class FormStatSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    language_display = serializers.CharField(source='get_language_display', read_only=True)

    class Meta:
        model = Form
        fields = ('name', 'code', 'country_id', 'language', 'language_display', 'id',)


class ListFormSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    country = RegoCountrySerializer()
    user = UserSerializer()
    language_display = serializers.CharField(source='get_language_display', read_only=True)

    class Meta:
        model = Form
        fields = ('name', 'code', 'updated_at', 'user', 'country', 'language', 'language_display', 'id',)


class ListFormDataSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    selected_option_display = serializers.CharField(source='get_selected_option_display', read_only=True)

    class Meta:
        model = FormData
        fields = ('form', 'question_id', 'selected_option', 'selected_option_display', 'notes')


class ListNiceDocSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    country = RegoCountrySerializer()
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)

    class Meta:
        model = NiceDocument
        fields = ('name', 'country', 'document', 'document_url', 'visibility', 'visibility_display')


class ShortFormSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    country = RegoCountrySerializer()
    language_display = serializers.CharField(source='get_language_display', read_only=True)

    class Meta:
        model = Form
        fields = ('name', 'code', 'updated_at', 'country', 'language', 'language_display', 'id',)


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


class NSPhaseSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    phase_display = serializers.CharField(source='get_phase_display', read_only=True)

    class Meta:
        model = NSPhase
        fields = ('id', 'country', 'phase', 'phase_display', 'updated_at')


class MiniUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')


class WorkPlanSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    user = MiniUserSerializer()
    prioritization_display = serializers.CharField(source='get_prioritization_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = WorkPlan
        fields = '__all__'


class OverviewSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    user = MiniUserSerializer()
    country = RegoCountrySerializer()
    type_of_capacity_assessment_display = serializers.CharField(
        source='get_type_of_capacity_assessment_display', read_only=True)
    type_of_last_capacity_assessment_display = serializers.CharField(
        source='get_type_of_last_capacity_assessment_display', read_only=True)

    class Meta:
        model = Overview
        fields = '__all__'
