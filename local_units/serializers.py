import json
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from .models import LocalUnit, LocalUnitType
from api.models import Country


class CountrySerializer(ModelSerializer):

    class Meta:
        model = Country
        fields = (
            'name', 'iso3'
        )

class LocalUnitTypeSerializer(ModelSerializer):

    class Meta:
        model = LocalUnitType
        fields = (
            'name', 'level'
        )

class LocalUnitSerializer(ModelSerializer):
    location = SerializerMethodField()
    country = CountrySerializer()
    type = LocalUnitTypeSerializer()
    class Meta:
        model = LocalUnit
        fields = [
            'local_branch_name', 'english_branch_name', 'type', 'country',
            'created_at', 'modified_at', 'draft', 'validated', 'postcode',
            'address_loc', 'address_en', 'city_loc', 'city_en', 'link',
            'location', 'focal_person_loc', 'focal_person_en',
            'source_loc', 'source_en'
            # 'email', 'phone',
            ]

    def get_location(self, unit):
        return json.loads(unit.location.geojson)
    
    def get_country(self, unit):
        return {'country'}

    def get_type(self, unit):
        return {'type'}
