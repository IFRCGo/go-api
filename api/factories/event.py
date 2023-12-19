import factory
from factory import fuzzy
import datetime
import pytz

from ..models import (
    AlertLevel,

    Event,
    EventFeaturedDocument,
    EventLink,
    Appeal,
)
from .disaster_type import DisasterTypeFactory
from api.factories.country import CountryFactory


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    name = fuzzy.FuzzyText(length=50, prefix='event-')
    slug = fuzzy.FuzzyText(length=50)
    dtype = factory.SubFactory(DisasterTypeFactory)

    @factory.post_generation
    def districts(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for district in extracted:
                self.districts.add(district)

    @factory.post_generation
    def countries(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for country in extracted:
                self.countries.add(country)

    @factory.post_generation
    def regions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for region in extracted:
                self.regions.add(region)

    parent_event = factory.SubFactory(
        "api.factories.event.EventFactory", parent_event=None
    )

    summary = fuzzy.FuzzyText(length=500)

    num_injured = fuzzy.FuzzyInteger(0)
    num_dead = fuzzy.FuzzyInteger(0)
    num_missing = fuzzy.FuzzyInteger(0)
    num_affected = fuzzy.FuzzyInteger(0)
    num_displaced = fuzzy.FuzzyInteger(0)

    ifrc_severity_level = fuzzy.FuzzyChoice(AlertLevel)
    glide = fuzzy.FuzzyText(length=18)

    disaster_start_date = fuzzy.FuzzyDateTime(
        datetime.datetime(2008, 1, 1, tzinfo=pytz.utc)
    )
    created_at = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    updated_at = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    previous_update = fuzzy.FuzzyDateTime(
        datetime.datetime(2008, 1, 1, tzinfo=pytz.utc)
    )

    auto_generated = fuzzy.FuzzyChoice([True, False])
    auto_generated_source = fuzzy.FuzzyText(length=50)

    is_featured = fuzzy.FuzzyChoice([True, False])
    is_featured_region = fuzzy.FuzzyChoice([True, False])

    hide_attached_field_reports = fuzzy.FuzzyChoice([True, False])
    hide_field_report_map = fuzzy.FuzzyChoice([True, False])

    tab_one_title = fuzzy.FuzzyText(length=50)
    tab_two_title = fuzzy.FuzzyText(length=50)
    tab_three_title = fuzzy.FuzzyText(length=50)
    visibility = 3


class EventFeaturedDocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EventFeaturedDocument

    event = factory.SubFactory(Event)
    title = fuzzy.FuzzyText(length=50, prefix='event-featured-document-title-')
    description = fuzzy.FuzzyText(length=100, prefix='event-featured-document-description-')


class EventLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EventLink

    event = factory.SubFactory(Event)
    title = fuzzy.FuzzyText(length=50, prefix='event-link-title-')
    description = fuzzy.FuzzyText(length=100, prefix='event-link-description-')


class AppealFactory(factory.django.DjangoModelFactory):
    name = fuzzy.FuzzyText(length=50, prefix='event-')
    dtype = factory.SubFactory(DisasterTypeFactory)
    num_beneficiaries = fuzzy.FuzzyInteger(0)
    amount_requested = fuzzy.FuzzyInteger(0)
    amount_funded = fuzzy.FuzzyInteger(0)
    event = factory.SubFactory(EventFactory)
    country = factory.SubFactory(CountryFactory)
    class Meta:
        model = Appeal
