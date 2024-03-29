import json
from rest_framework import serializers

from .models import (
    LocalUnit,
    LocalUnitType,
    LocalUnitLevel,
    DelegationOffice,
    DelegationOfficeType,
)
from api.models import Country


class LocalUnitCountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = (
            'name', 'iso3'
        )


class LocalUnitTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = LocalUnitType
        fields = (
            'name', 'code', 'id'
        )


class LocalUnitLevelSerializer(serializers.ModelSerializer):

    class Meta:
        model = LocalUnitLevel
        fields = (
            'name', 'level', 'id'
        )


class LocalUnitSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    country = LocalUnitCountrySerializer()
    type = LocalUnitTypeSerializer()
    level = LocalUnitLevelSerializer()

    class Meta:
        model = LocalUnit
        fields = [
            'local_branch_name', 'english_branch_name', 'type', 'country',
            'created_at', 'modified_at', 'draft', 'validated', 'postcode',
            'address_loc', 'address_en', 'city_loc', 'city_en', 'link',
            'location', 'focal_person_loc', 'focal_person_en',
            'source_loc', 'source_en', 'subtype', 'date_of_data',
            'email', 'phone', 'level'
            ]

    def get_location(self, unit):
        return json.loads(unit.location.geojson)

    def get_country(self, unit):
        return {'country'}

    def get_type(self, unit):
        return {'type'}


class DelegationOfficeCountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = (
            'name', 'iso3', 'region', 'region'
        )


class DelegationOfficeTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = DelegationOfficeType
        fields = (
            'name', 'code'
        )


class DelegationOfficeSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    country = DelegationOfficeCountrySerializer()
    dotype = DelegationOfficeTypeSerializer()

    class Meta:
        model = DelegationOffice
        fields = [
            'name',
            'city',
            'address',
            'postcode',
            'location',
            'society_url',
            'url_ifrc',
            'hod_first_name',
            'hod_last_name',
            'hod_mobile_number',
            'hod_email',
            'assistant_name',
            'assistant_email',
            'is_ns_same_location',
            'is_multiple_ifrc_offices',
            'is_public',
            'created_at',
            'modified_at',
            'date_of_data',
            'country',
            'dotype']

    def get_location(self, office):
        return json.loads(office.location.geojson)

    def get_country(self, office):
        return {'country'}

    def get_type(self, office):
        return {'type'}

class LocalUnitOptionsSerializer(serializers.Serializer):
    type = LocalUnitTypeSerializer(many=True)
    level = LocalUnitLevelSerializer(many=True)


class MiniDelegationOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DelegationOffice
        fields = (
            'hod_first_name',
            'hod_last_name',
            'hod_mobile_number',
            'hod_email',
        )
