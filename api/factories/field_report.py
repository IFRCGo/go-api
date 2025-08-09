import datetime

import factory
import pytz
from factory import fuzzy

from .. import models
from . import disaster_type, event


class FieldReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FieldReport

    is_covid_report = fuzzy.FuzzyChoice([True, False])
    rid = fuzzy.FuzzyText(length=100)
    dtype = factory.SubFactory(disaster_type.DisasterTypeFactory)
    event = factory.SubFactory(event.EventFactory)
    summary = fuzzy.FuzzyText(length=500)
    title = fuzzy.FuzzyText(length=10, prefix="title-")
    description = fuzzy.FuzzyText(length=200)
    report_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    # start_date is now what the user explicitly sets while filling the Field Report form.
    start_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    created_at = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    updated_at = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    previous_update = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))
    status = fuzzy.FuzzyInteger(0)

    request_assistance = False  # fuzzy.FuzzyChoice([True, False])
    ns_request_assistance = False  # fuzzy.FuzzyChoice([True, False])

    num_injured = fuzzy.FuzzyInteger(0, 9)
    num_dead = fuzzy.FuzzyInteger(0, 9)
    num_missing = fuzzy.FuzzyInteger(0, 9)
    num_affected = fuzzy.FuzzyInteger(0, 9)
    num_displaced = fuzzy.FuzzyInteger(0, 9)
    num_assisted = fuzzy.FuzzyInteger(0, 9)
    num_localstaff = fuzzy.FuzzyInteger(0, 9)
    num_volunteers = fuzzy.FuzzyInteger(0, 9)
    num_expats_delegates = fuzzy.FuzzyInteger(0, 9)

    # Early Warning fields
    num_potentially_affected = fuzzy.FuzzyInteger(0, 9)
    num_highest_risk = fuzzy.FuzzyInteger(0, 9)
    affected_pop_centres = fuzzy.FuzzyText(length=500)

    gov_num_injured = fuzzy.FuzzyInteger(0, 9)
    gov_num_dead = fuzzy.FuzzyInteger(0, 9)
    gov_num_missing = fuzzy.FuzzyInteger(0, 9)
    gov_num_affected = fuzzy.FuzzyInteger(0, 9)
    gov_num_displaced = fuzzy.FuzzyInteger(0, 9)
    gov_num_assisted = fuzzy.FuzzyInteger(0, 9)

    # Epidemic fields
    epi_cases = fuzzy.FuzzyInteger(0, 9)
    epi_suspected_cases = fuzzy.FuzzyInteger(0, 9)
    epi_probable_cases = fuzzy.FuzzyInteger(0, 9)
    epi_confirmed_cases = fuzzy.FuzzyInteger(0, 9)
    epi_num_dead = fuzzy.FuzzyInteger(0, 9)
    epi_figures_source = fuzzy.FuzzyChoice(models.EPISourceChoices)
    epi_cases_since_last_fr = fuzzy.FuzzyInteger(0, 9)
    epi_deaths_since_last_fr = fuzzy.FuzzyInteger(0, 9)
    epi_notes_since_last_fr = fuzzy.FuzzyText(length=50)

    who_num_assisted = fuzzy.FuzzyInteger(0, 9)
    health_min_num_assisted = fuzzy.FuzzyInteger(0, 9)

    # Early Warning fields
    gov_num_potentially_affected = fuzzy.FuzzyInteger(0, 9)
    gov_num_highest_risk = fuzzy.FuzzyInteger(0, 9)
    gov_affected_pop_centres = fuzzy.FuzzyText(length=500)

    other_num_injured = fuzzy.FuzzyInteger(0, 9)
    other_num_dead = fuzzy.FuzzyInteger(0, 9)
    other_num_missing = fuzzy.FuzzyInteger(0, 9)
    other_num_affected = fuzzy.FuzzyInteger(0, 9)
    other_num_displaced = fuzzy.FuzzyInteger(0, 9)
    other_num_assisted = fuzzy.FuzzyInteger(0, 9)

    # Early Warning fields
    other_num_potentially_affected = fuzzy.FuzzyInteger(0, 9)
    other_num_highest_risk = fuzzy.FuzzyInteger(0, 9)
    other_affected_pop_centres = fuzzy.FuzzyText(length=500)

    # Date of data for situation fields
    sit_fields_date = fuzzy.FuzzyDateTime(datetime.datetime(2008, 1, 1, tzinfo=pytz.utc))

    # Text field for users to specify sources for where they have marked 'Other' as source.
    other_sources = fuzzy.FuzzyText(length=50)

    # actions taken
    actions_others = fuzzy.FuzzyText(length=50)

    # visibility
    visibility = fuzzy.FuzzyChoice(models.VisibilityChoices)

    # information
    bulletin = fuzzy.FuzzyChoice(models.RequestChoices)
    dref = fuzzy.FuzzyChoice(models.RequestChoices)
    dref_amount = fuzzy.FuzzyInteger(0, 9999)
    appeal = fuzzy.FuzzyChoice(models.RequestChoices)
    appeal_amount = fuzzy.FuzzyInteger(0, 9999)
    imminent_dref = fuzzy.FuzzyChoice(models.RequestChoices)
    imminent_dref_amount = fuzzy.FuzzyInteger(0, 9999)
    forecast_based_action = fuzzy.FuzzyChoice(models.RequestChoices)  # only EW
    forecast_based_action_amount = fuzzy.FuzzyInteger(0, 9999)  # only EW

    # disaster response
    rdrt = fuzzy.FuzzyChoice(models.RequestChoices)
    num_rdrt = fuzzy.FuzzyInteger(0, 9)
    fact = fuzzy.FuzzyChoice(models.RequestChoices)
    num_fact = fuzzy.FuzzyInteger(0, 9)
    ifrc_staff = fuzzy.FuzzyChoice(models.RequestChoices)
    num_ifrc_staff = fuzzy.FuzzyInteger(0, 9)
    emergency_response_unit = fuzzy.FuzzyChoice(models.RequestChoices)
    num_emergency_response_unit = fuzzy.FuzzyInteger(0, 9)

    # ERU units
    eru_base_camp = fuzzy.FuzzyChoice(models.RequestChoices)
    eru_base_camp_units = fuzzy.FuzzyInteger(0, 9)

    eru_basic_health_care = fuzzy.FuzzyChoice(models.RequestChoices)
    eru_basic_health_care_units = fuzzy.FuzzyInteger(0, 9)

    eru_it_telecom = fuzzy.FuzzyChoice(models.RequestChoices)
    eru_it_telecom_units = fuzzy.FuzzyInteger(0, 9)

    eru_logistics = fuzzy.FuzzyChoice(models.RequestChoices)
    eru_logistics_units = fuzzy.FuzzyInteger(0, 9)

    eru_deployment_hospital = fuzzy.FuzzyChoice(models.RequestChoices)
    eru_deployment_hospital_units = fuzzy.FuzzyInteger(0, 9)

    eru_referral_hospital = fuzzy.FuzzyChoice(models.RequestChoices)
    eru_referral_hospital_units = fuzzy.FuzzyInteger(0, 9)

    eru_relief = fuzzy.FuzzyChoice(models.RequestChoices)
    eru_relief_units = fuzzy.FuzzyInteger(0, 9)

    eru_water_sanitation_15 = fuzzy.FuzzyChoice(models.RequestChoices)
    eru_water_sanitation_15_units = fuzzy.FuzzyInteger(0, 9)

    eru_water_sanitation_40 = fuzzy.FuzzyChoice(models.RequestChoices)
    eru_water_sanitation_40_units = fuzzy.FuzzyInteger(0, 9)

    eru_water_sanitation_20 = fuzzy.FuzzyChoice(models.RequestChoices)
    eru_water_sanitation_20_units = fuzzy.FuzzyInteger(0, 9)

    notes_health = fuzzy.FuzzyText(length=50)
    notes_ns = fuzzy.FuzzyText(length=50)
    notes_socioeco = fuzzy.FuzzyText(length=50)


# If we use the below ones, double save will occur – breaks tests.
# See https://github.com/FactoryBoy/factory_boy/issues/316
#
#    @factory.post_generation
#    def districts(self, create, extracted, **kwargs):
#        if not create:
#            return
#
#        if extracted:
#            for district in extracted:
#                self.districts.add(district)
#
#    @factory.post_generation
#    def countries(self, create, extracted, **kwargs):
#        if not create:
#            return
#
#        if extracted:
#            for country in extracted:
#                self.countries.add(country)
#
#    @factory.post_generation
#    def regions(self, create, extracted, **kwargs):
#        if not create:
#            return
#
#        if extracted:
#            for region in extracted:
#                self.regions.add(region)
#
#    @factory.post_generation
#    def external_partners(self, create, extracted, **kwargs):
#        if not create:
#            return
#
#        if extracted:
#            for external_partner in extracted:
#                self.external_partners.add(external_partner)
#
#    @factory.post_generation
#    def supported_activities(self, create, extracted, **kwargs):
#        if not create:
#            return
#
#        if extracted:
#            for supported_activity in extracted:
#                self.supported_activities.add(supported_activity)
#
