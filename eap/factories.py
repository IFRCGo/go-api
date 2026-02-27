from datetime import datetime

import factory
import pytz
from factory import fuzzy

from eap.models import (
    EAPContact,
    EAPFile,
    EAPRegistration,
    EAPStatus,
    EAPType,
    EnablingApproach,
    FullEAP,
    KeyActor,
    OperationActivity,
    PlannedOperation,
    SimplifiedEAP,
    TimeFrame,
)


class EAPFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EAPFile

    caption = fuzzy.FuzzyText(length=10, prefix="EAPFile-")
    file = factory.django.FileField(filename="eap_file.txt")

    @classmethod
    def _create_image(cls, *args, **kwargs) -> EAPFile:
        return cls.create(
            file=factory.django.FileField(filename="eap_image.jpeg", data=b"fake image data"),
            caption="EAP Image",
            **kwargs,
        )

    @classmethod
    def _create_file(cls, *args, **kwargs) -> EAPFile:
        return cls.create(
            file=factory.django.FileField(filename="eap_document.pdf", data=b"fake pdf data"),
            caption="EAP Document",
            **kwargs,
        )


class EAPContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EAPContact

    title = fuzzy.FuzzyText(length=5, prefix="Title-")
    name = fuzzy.FuzzyText(length=10, prefix="Contact-")
    email = factory.LazyAttribute(lambda obj: f"{obj.name.lower()}@example.com")
    phone_number = fuzzy.FuzzyText(length=10, prefix="12345")


class EAPRegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EAPRegistration

    status = fuzzy.FuzzyChoice(EAPStatus)
    eap_type = fuzzy.FuzzyChoice(EAPType)
    national_society_contact_name = fuzzy.FuzzyText(length=10, prefix="NS-")
    national_society_contact_email = factory.LazyAttribute(lambda obj: f"{obj.national_society_contact_name.lower()}@example.com")

    @factory.post_generation
    def partners(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for partner in extracted:
                self.partners.add(partner)


class SimplifiedEAPFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SimplifiedEAP

    seap_timeframe = fuzzy.FuzzyInteger(2)
    total_budget = fuzzy.FuzzyInteger(1000, 1000000)
    readiness_budget = fuzzy.FuzzyInteger(1000, 1000000)
    pre_positioning_budget = fuzzy.FuzzyInteger(1000, 1000000)
    early_action_budget = fuzzy.FuzzyInteger(1000, 1000000)
    people_targeted = fuzzy.FuzzyInteger(2001, 100000)
    seap_lead_timeframe_unit = fuzzy.FuzzyInteger(TimeFrame.MONTHS)
    seap_lead_time = fuzzy.FuzzyInteger(1, 12)
    operational_timeframe = fuzzy.FuzzyInteger(1, 12)
    national_society_contact_name = fuzzy.FuzzyText(length=10, prefix="NS-")
    national_society_contact_email = factory.LazyAttribute(lambda obj: f"{obj.national_society_contact_name.lower()}@example.com")
    ifrc_delegation_focal_point_name = fuzzy.FuzzyText(length=10, prefix="IFRC-")
    ifrc_delegation_focal_point_email = factory.LazyAttribute(
        lambda obj: f"{obj.ifrc_delegation_focal_point_name.lower()}@example.com"
    )
    ifrc_head_of_delegation_name = fuzzy.FuzzyText(length=10, prefix="ifrc-head-")
    ifrc_head_of_delegation_email = factory.LazyAttribute(lambda obj: f"{obj.ifrc_head_of_delegation_name.lower()}@example.com")
    prioritized_hazard_and_impact = fuzzy.FuzzyText(length=50, prefix="prioritized-hazard")
    risks_selected_protocols = fuzzy.FuzzyText(length=50, prefix="risks-selected-")
    selected_early_actions = fuzzy.FuzzyText(length=50, prefix="selected-early-")
    overall_objective_intervention = fuzzy.FuzzyText(length=20, prefix="overall-objective-")
    potential_geographical_high_risk_areas = fuzzy.FuzzyText(length=20, prefix="potential-geographical-")
    assisted_through_operation = fuzzy.FuzzyText(length=20, prefix="assisted-through-")
    trigger_threshold_justification = fuzzy.FuzzyText(length=50, prefix="trigger-threshold-")
    next_step_towards_full_eap = fuzzy.FuzzyText(length=50, prefix="next-step-")
    early_action_capability = fuzzy.FuzzyText(length=50, prefix="early-action-")
    rcrc_movement_involvement = fuzzy.FuzzyText(length=50, prefix="rcrc-movement-")

    @factory.post_generation
    def enabling_approaches(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for approach in extracted:
                self.enabling_approaches.add(approach)

    @factory.post_generation
    def planned_operations(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for operation in extracted:
                self.planned_operations.add(operation)


class OperationActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OperationActivity

    activity = fuzzy.FuzzyText(length=50, prefix="Activity-")
    timeframe = fuzzy.FuzzyChoice(TimeFrame)


class EnablingApproachFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EnablingApproach

    approach = fuzzy.FuzzyChoice(EnablingApproach.Approach)
    budget_per_approach = fuzzy.FuzzyInteger(1000, 1000000)
    ap_code = fuzzy.FuzzyInteger(100, 999)

    @factory.post_generation
    def readiness_activities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for activity in extracted:
                self.readiness_activities.add(activity)

    @factory.post_generation
    def prepositioning_activities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for activity in extracted:
                self.prepositioning_activities.add(activity)

    @factory.post_generation
    def early_action_activities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for activity in extracted:
                self.early_action_activities.add(activity)


class PlannedOperationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlannedOperation

    sector = fuzzy.FuzzyChoice(PlannedOperation.Sector)
    people_targeted = fuzzy.FuzzyInteger(100, 100000)
    budget_per_sector = fuzzy.FuzzyInteger(1000, 1000000)
    ap_code = fuzzy.FuzzyInteger(100, 999)

    @factory.post_generation
    def readiness_activities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for activity in extracted:
                self.readiness_activities.add(activity)

    @factory.post_generation
    def prepositioning_activities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for activity in extracted:
                self.prepositioning_activities.add(activity)

    @factory.post_generation
    def early_action_activities(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for activity in extracted:
                self.early_action_activities.add(activity)


class KeyActorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = KeyActor

    description = fuzzy.FuzzyText(length=5, prefix="KeyActor-")


class FullEAPFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FullEAP

    expected_submission_time = fuzzy.FuzzyDateTime(datetime(2025, 1, 1, tzinfo=pytz.utc))
    lead_time = fuzzy.FuzzyInteger(1, 100)
    total_budget = fuzzy.FuzzyInteger(1000, 1000000)
    readiness_budget = fuzzy.FuzzyInteger(1000, 1000000)
    pre_positioning_budget = fuzzy.FuzzyInteger(1000, 1000000)
    early_action_budget = fuzzy.FuzzyInteger(1000, 1000000)
    people_targeted = fuzzy.FuzzyInteger(10001, 10000000)
    national_society_contact_name = fuzzy.FuzzyText(length=10, prefix="NS-")
    national_society_contact_email = factory.LazyAttribute(lambda obj: f"{obj.national_society_contact_name.lower()}@example.com")
    ifrc_delegation_focal_point_name = fuzzy.FuzzyText(length=10, prefix="IFRC-")
    ifrc_delegation_focal_point_email = factory.LazyAttribute(
        lambda obj: f"{obj.ifrc_delegation_focal_point_name.lower()}@example.com"
    )
    ifrc_head_of_delegation_name = fuzzy.FuzzyText(length=10, prefix="ifrc-head-")
    ifrc_head_of_delegation_email = factory.LazyAttribute(lambda obj: f"{obj.ifrc_head_of_delegation_name.lower()}@example.com")

    @factory.post_generation
    def key_actors(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for actor in extracted:
                self.key_actors.add(actor)
