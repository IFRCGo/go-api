from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .forms import CountryOverviewForm, SeasonalCalenderForm
from .models import (
    Month,
    CountryOverview,

    SocialEvent,
    KeyClimateEvent,
    SeasonalCalender,
)


class SocialEventInline(admin.TabularInline):
    model = SocialEvent


class KeyClimateEventByInline(admin.TabularInline):
    model = KeyClimateEvent
    max_num = len(Month.CHOICES)


class SeasonalCalenderInine(admin.TabularInline):
    model = SeasonalCalender
    form = SeasonalCalenderForm


@admin.register(CountryOverview)
class CountryOverviewAdmin(admin.ModelAdmin):
    autocomplete_fields = ('country',)
    search_fields = ('country__name',)
    list_display = ('country',)
    inlines = [
        SocialEventInline, KeyClimateEventByInline, SeasonalCalenderInine,
    ]
    form = CountryOverviewForm
    fieldsets = (
        (None, {'fields': ('country',)}),
        (_('COUNTRY KEY INDICATORS (SOURCE: FDRS)'), {
            'fields': (
                'population', 'urban_population', 'gdp',
                'gnipc', 'poverty', 'life_expectancy', 'literacy',
            )
        }),
        (_('NATIONAL SOCIETY INDICATORS (SOURCE: FDRS)'), {
            'fields': ('income', 'expenditures', 'volunteers', 'trained_in_first_aid'),
        }),
        (_('KEY CLIMATE EVENT'), {'fields': ('avg_temperature', 'avg_rainfall_precipitation', 'rainy_season')}),
    )
