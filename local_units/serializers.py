import json
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from .models import LocalUnit
from api.models import Country


class CountrySerializer(ModelSerializer):

    class Meta:
        model = Country
        fields = (
            'name', 'iso3'
        )

class LocalUnitSerializer(ModelSerializer):
    location = SerializerMethodField()
    country = CountrySerializer()
    class Meta:
        model = LocalUnit
        fields = [
            'unique_id', 'national_society_name', 'local_branch_name', 'english_branch_name',
            'branch_level', 'branch_type_name', 'created_at', 'modified_at', 'draft', 'validated',
            'source', 'address', 'post_code', 'phone', 'link', 'location', 'country'
            ]

    def get_location(self, unit):
        return json.loads(unit.location.geojson)
    
    def get_country(self, unit):
        return {'country'}
