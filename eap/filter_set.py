import django_filters as filters

from eap.models import DevelopmentRegistrationEAP, EAPType
from api.models import Country, DisasterType


class BaseEAPFilterSet(filters.FilterSet):
    created_at__lte = filters.DateFilter(
        field_name="created_at", lookup_expr="lte", input_formats=["%Y-%m-%d"]
    )
    created_at__gte = filters.DateFilter(
        field_name="created_at", lookup_expr="gte", input_formats=["%Y-%m-%d"]
    )
    # Country
    country = filters.ModelMultipleChoiceFilter(
        field_name="country",
        queryset=Country.objects.all(),
    )
    national_society = filters.ModelMultipleChoiceFilter(
        field_name="national_society",
        queryset=Country.objects.all(),
    )
    region = filters.NumberFilter(field_name="country__region_id", label="Region")
    partners = filters.ModelMultipleChoiceFilter(
        field_name="partners",
        queryset=Country.objects.all(),
    )

    # Disaster
    disaster_type = filters.ModelMultipleChoiceFilter(
        field_name="disaster_type",
        queryset=DisasterType.objects.all(),
    )


class DevelopmentRegistrationEAPFilterSet(BaseEAPFilterSet):
    eap_type = filters.ChoiceFilter(
        choices=EAPType.choices,
        label="EAP Type",
    )

    class Meta:
        model = DevelopmentRegistrationEAP
        fields = ()
