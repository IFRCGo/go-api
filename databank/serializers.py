from rest_framework import serializers

from api.models import (
    Appeal,
    Country,
    District,
)
from api.serializers import DisasterTypeSerializer
from .models import (
    CountryOverview,

    SocialEvent,
    KeyClimateEvent,
    SeasonalCalender,
    KeyDocument,
    ExternalSource,
)


class KeyClimateEventSerializer(serializers.ModelSerializer):
    month_display = serializers.CharField(source='get_month_display', read_only=True)

    class Meta:
        model = KeyClimateEvent
        exclude = ('overview',)


class SeasonalCalenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonalCalender
        exclude = ('overview',)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('name', 'iso',)


class SocialEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialEvent
        exclude = ('overview',)


class AppealSerializer(serializers.ModelSerializer):
    dtype = DisasterTypeSerializer()
    event_name = serializers.CharField(source='event.name', read_only=True)

    class Meta:
        model = Appeal
        fields = (
            'event_name', 'dtype', 'start_date',
            'num_beneficiaries', 'amount_requested', 'amount_funded',
        )


class WBDistrictPopulationSerializer(serializers.ModelSerializer):
    population = serializers.IntegerField(source='wb_population')
    year = serializers.CharField(source='wb_year')

    class Meta:
        model = District
        fields = ('id', 'name', 'code', 'population', 'year')


class WBCountryPopulationSerializer(WBDistrictPopulationSerializer):
    districts = WBDistrictPopulationSerializer(source='district_set', many=True)

    class Meta:
        model = Country
        fields = ('id', 'iso', 'iso3', 'name', 'population', 'year', 'districts')


class KeyDocumentSerializer(serializers.ModelSerializer):
    group_display = serializers.CharField(source='group.title', read_only=True)

    class Meta:
        model = KeyDocument
        exclude = ('overview',)


class ExternalSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalSource
        exclude = ('overview',)


class CountryOverviewSerializer(serializers.ModelSerializer):
    school_status_display = serializers.CharField(source='get_school_status_display', read_only=True)
    rainy_season_display = serializers.CharField(source='get_rainy_season_display', read_only=True)
    past_crises_events_count = serializers.IntegerField(read_only=True)
    wb_population = WBCountryPopulationSerializer(source='country', read_only=True)

    social_events = SocialEventSerializer(source='socialevent_set', many=True, read_only=True)
    climate_events = KeyClimateEventSerializer(source='keyclimateevent_set', many=True, read_only=True)
    seasonal_calender = SeasonalCalenderSerializer(source='seasonalcalender_set', many=True, read_only=True)
    appeals = AppealSerializer(many=True, read_only=True)
    key_documents = KeyDocumentSerializer(source='keydocument_set', many=True, read_only=True)
    external_sources = ExternalSourceSerializer(source='externalsource_set', many=True, read_only=True)

    class Meta:
        model = CountryOverview
        fields = '__all__'
