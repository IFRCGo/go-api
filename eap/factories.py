import datetime
import factory
from factory import fuzzy
from datetime import timezone

from django.core.files.base import ContentFile

from api.factories import (
    disaster_type,
    country,
    district,
)

from .models import (
    EAP,
    EAPDocument,
)


class EAPDocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EAPDocument

    file = factory.LazyAttribute(
        lambda _: ContentFile(
            factory.django.ImageField()._make_data(
                {'width': 1024, 'height': 768}
            ), 'flash_update.jpg'
        )
    )


class EAPFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EAP

    district = factory.SubFactory(district.DistrictFactory)
    country = factory.SubFactory(country.CountryFactory)
    disaster_type = factory.SubFactory(disaster_type.DisasterTypeFactory)
    document = factory.SubFactory(EAPDocumentFactory)
    eap_number = fuzzy.FuzzyText(length=20)
    approval_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=timezone.utc))
    status = fuzzy.FuzzyChoice(EAP.Status)
    operational_timeframe = fuzzy.FuzzyInteger(0, 2)
    lead_time = fuzzy.FuzzyInteger(0, 2)
    eap_timeframe = fuzzy.FuzzyInteger(0, 2)
    num_of_people = fuzzy.FuzzyInteger(0, 5)
    total_budget = fuzzy.FuzzyInteger(0, 5)
    readiness_budget = fuzzy.FuzzyInteger(0, 5)
    pre_positioning_budget = fuzzy.FuzzyInteger(0, 5)
    early_action_budget = fuzzy.FuzzyInteger(0, 5)
    trigger_statement = fuzzy.FuzzyText(length=20)
    overview = fuzzy.FuzzyText(length=50)
    originator_name = fuzzy.FuzzyText(length=50)
    originator_title = fuzzy.FuzzyText(length=50)
    originator_email = fuzzy.FuzzyText(length=50)
    originator_phone = fuzzy.FuzzyInteger(0, 9)

    nsc_name = fuzzy.FuzzyText(length=50)
    nsc_title = fuzzy.FuzzyText(length=50)
    nsc_email = fuzzy.FuzzyText(length=50)
    nsc_phone = fuzzy.FuzzyInteger(0, 9)

    ifrc_focal_name = fuzzy.FuzzyText(length=50)
    ifrc_focal_title = fuzzy.FuzzyText(length=50)
    ifrc_focal_email = fuzzy.FuzzyText(length=50)
    ifrc_focal_phone = fuzzy.FuzzyInteger(0, 9)

    @factory.post_generation
    def early_actions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for early_action in extracted:
                self.early_actions.add(early_action)
