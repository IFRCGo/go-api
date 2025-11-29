import django_filters as filters

from api.models import Country, Region
from notifications.models import AlertSubscription


class AlertSubscriptionFilterSet(filters.FilterSet):
    country = filters.ModelMultipleChoiceFilter(field_name="countries", queryset=Country.objects.all())
    region = filters.ModelMultipleChoiceFilter(field_name="regions", queryset=Region.objects.all())
    alert_source = filters.NumberFilter(field_name="alert_source", label="Alert Source")
    hazard_type = filters.NumberFilter(field_name="hazard_types__type", label="Hazard Type")
    alert_per_day = filters.ChoiceFilter(choices=AlertSubscription.AlertPerDay.choices, label="Alert Per Day")

    class Meta:
        model = AlertSubscription
        fields = {
            "countries__iso3": ("exact",),
            "alert_per_day": ("exact",),
        }
