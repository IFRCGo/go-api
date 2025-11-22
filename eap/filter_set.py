import django_filters as filters

from api.models import Country, DisasterType
from eap.models import EAPRegistration, EAPStatus, EAPType, SimplifiedEAP


class BaseEAPFilterSet(filters.FilterSet):
    created_at__lte = filters.DateFilter(field_name="created_at", lookup_expr="lte", input_formats=["%Y-%m-%d"])
    created_at__gte = filters.DateFilter(field_name="created_at", lookup_expr="gte", input_formats=["%Y-%m-%d"])
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


class EAPRegistrationFilterSet(BaseEAPFilterSet):
    eap_type = filters.ChoiceFilter(
        choices=EAPType.choices,
        label="EAP Type",
    )
    status = filters.ChoiceFilter(
        choices=EAPStatus.choices,
        label="EAP Status",
    )

    class Meta:
        model = EAPRegistration
        fields = ()


class SimplifiedEAPFilterSet(BaseEAPFilterSet):
    class Meta:
        model = SimplifiedEAP
        fields = ("eap_registration",)
