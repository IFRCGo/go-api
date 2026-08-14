from datetime import date

from django.test import TestCase, override_settings

from dref.factories.dref import (
    DrefFactory,
    DrefFinalReportFactory,
    DrefOperationalUpdateFactory,
    IdentifiedNeedFactory,
    PlannedInterventionFactory,
)
from dref.models import Dref, DrefSummary, IdentifiedNeed
from dref.summary import SUMMARY_FIELDS, DrefSummaryGenerator
from dref.tasks import DrefSummaryGenerationResult, generate_dref_summary
from main.llm import (
    AzureOpenAiChat,
    DummyDrefSummaryLLMClient,
    get_dref_summary_llm_client,
)


class DrefSummaryLLMClientTest(TestCase):
    def test_uses_dummy_client_during_tests_by_default(self):
        # settings.TESTING is always true under the test runner, so the
        # factory should return the dummy client even though
        # USE_DUMMY_LLM_CLIENT itself defaults to False.
        self.assertIsInstance(get_dref_summary_llm_client(), DummyDrefSummaryLLMClient)

    @override_settings(
        TESTING=False,
        USE_DUMMY_LLM_CLIENT=False,
        AZURE_OPENAI_ENDPOINT="https://example.com",
        AZURE_OPENAI_API_KEY="fake-key",
        AZURE_OPENAI_DEPLOYMENT_NAME="fake-deployment",
    )
    def test_uses_real_client_when_flag_off_and_not_testing(self):
        self.assertIsInstance(get_dref_summary_llm_client(), AzureOpenAiChat)

    @override_settings(TESTING=False, USE_DUMMY_LLM_CLIENT=True)
    def test_uses_dummy_client_when_flag_on(self):
        self.assertIsInstance(get_dref_summary_llm_client(), DummyDrefSummaryLLMClient)


class DrefSummaryGeneratorTest(TestCase):
    def test_generate_all_succeeds_end_to_end_for_dref(self):
        dref = DrefFactory.create(title="Test Dref")

        results = DrefSummaryGenerator().generate_all(dref)

        self.assertEqual(set(results.keys()), set(SUMMARY_FIELDS))
        self.assertIn("DUMMY RESPONSE", results["situational_overview"])

    def test_generate_all_succeeds_end_to_end_for_dref_operational_update(self):
        ops_update = DrefOperationalUpdateFactory.create(dref=DrefFactory.create(), title="Test Ops Update")

        results = DrefSummaryGenerator().generate_all(ops_update)

        self.assertEqual(set(results.keys()), set(SUMMARY_FIELDS))
        self.assertIn("DUMMY RESPONSE", results["situational_overview"])

    def test_generate_all_succeeds_end_to_end_for_dref_final_report(self):
        planned_intervention = PlannedInterventionFactory.create(challenges="Some challenge", lessons_learnt="Some lesson")
        final_report = DrefFinalReportFactory.create(title="Test Final Report", planned_interventions=[planned_intervention])

        results = DrefSummaryGenerator().generate_all(final_report)

        self.assertEqual(set(results.keys()), set(SUMMARY_FIELDS))
        self.assertIn("DUMMY RESPONSE", results["situational_overview"])
        self.assertIn("DUMMY RESPONSE", results["challenges_identified"])
        self.assertIn("DUMMY RESPONSE", results["lessons_learned"])

    def test_get_section_kwargs_for_dref(self):
        dref = DrefFactory.create(
            title="Test Dref",
            event_description="Severe flooding",
            type_of_dref=Dref.DrefType.RESPONSE,
            event_scope="Affected 3 districts",
            operation_objective="Provide shelter",
            response_strategy="Cash and shelter support",
            total_targeted_population=5000,
            people_in_need=8000,
            people_assisted="5000 people",
            selection_criteria="Most vulnerable households",
            identified_gaps="No data for the eastern districts",
            needs_identified=[
                IdentifiedNeedFactory.create(
                    title=IdentifiedNeed.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
                    description="2000 households need emergency shelter",
                )
            ],
        )

        kwargs = DrefSummaryGenerator.get_section_kwargs(dref)

        self.assertEqual(
            set(kwargs.keys()),
            {"situational_overview", "needs_identified", "operational_strategy", "people_centered_approach"},
        )
        # Only the mapped (Figma) fields feed each section — no title/demographics/budget metadata.
        self.assertEqual(kwargs["situational_overview"]["event_description"], "Severe flooding")
        self.assertEqual(kwargs["situational_overview"]["event_scope"], "Affected 3 districts")
        self.assertNotIn("title", kwargs["situational_overview"])
        self.assertEqual(kwargs["operational_strategy"]["operation_objective"], "Provide shelter")
        self.assertEqual(kwargs["operational_strategy"]["response_strategy"], "Cash and shelter support")
        self.assertNotIn("total_targeted_population", kwargs["operational_strategy"])
        self.assertNotIn("people_in_need", kwargs["operational_strategy"])
        self.assertEqual(kwargs["people_centered_approach"]["people_assisted"], "5000 people")
        self.assertEqual(kwargs["people_centered_approach"]["selection_criteria"], "Most vulnerable households")
        self.assertNotIn("women", kwargs["people_centered_approach"])

        needs = kwargs["needs_identified"]["needs_identified"]
        self.assertEqual(len(needs), 1)
        self.assertEqual(needs[0]["title"], "Shelter Housing And Settlements")
        self.assertEqual(needs[0]["description"], "2000 households need emergency shelter")
        self.assertEqual(kwargs["needs_identified"]["identified_gaps"], "No data for the eastern districts")

    def test_get_section_kwargs_keeps_needs_without_description_and_drops_missing_gaps(self):
        # A need with no description still names the sector where a need exists, so it
        # is kept; identified_gaps is absent on the Final Report model entirely.
        dref = DrefFactory.create(
            type_of_dref=Dref.DrefType.RESPONSE,
            identified_gaps="",
            needs_identified=[IdentifiedNeedFactory.create(title=IdentifiedNeed.Title.HEALTH, description="")],
        )
        needs_section = DrefSummaryGenerator.get_section_kwargs(dref)["needs_identified"]
        self.assertEqual(needs_section["needs_identified"], [{"title": "Health"}])
        self.assertIsNone(needs_section["identified_gaps"])

        final_report = DrefFinalReportFactory.create(
            needs_identified=[IdentifiedNeedFactory.create(title=IdentifiedNeed.Title.EDUCATION, description="Schools closed")]
        )
        final_needs_section = DrefSummaryGenerator.get_section_kwargs(final_report)["needs_identified"]
        self.assertEqual(final_needs_section["needs_identified"], [{"title": "Education", "description": "Schools closed"}])
        self.assertIsNone(final_needs_section["identified_gaps"])

    def test_get_section_kwargs_for_dref_operational_update(self):
        ops_update = DrefOperationalUpdateFactory.create(
            dref=DrefFactory.create(),
            title="Test Ops Update",
            event_description="Flooding continues",
            operation_objective="Extend shelter support",
            response_strategy="Extended cash support",
            total_dref_allocation=100000,
            people_assisted="6000 people",
            selection_criteria="Vulnerable households",
            women=1000,
            men=900,
            girls=500,
            boys=600,
            new_operational_end_date=date(2025, 6, 1),
            total_operation_timeframe=6,
            identified_gaps="Assessment pending in two districts",
            needs_identified=[
                IdentifiedNeedFactory.create(
                    title=IdentifiedNeed.Title.HEALTH,
                    description="Mobile clinics still required",
                )
            ],
        )

        kwargs = DrefSummaryGenerator.get_section_kwargs(ops_update)

        self.assertEqual(
            set(kwargs.keys()),
            {"situational_overview", "needs_identified", "operational_strategy", "people_centered_approach"},
        )
        self.assertEqual(kwargs["needs_identified"]["needs_identified"][0]["description"], "Mobile clinics still required")
        self.assertEqual(kwargs["needs_identified"]["identified_gaps"], "Assessment pending in two districts")
        self.assertEqual(kwargs["situational_overview"]["event_description"], "Flooding continues")
        self.assertEqual(kwargs["operational_strategy"]["operation_objective"], "Extend shelter support")
        self.assertEqual(kwargs["operational_strategy"]["response_strategy"], "Extended cash support")
        # Non-mapped metadata (allocation, timeframe, demographics) is no longer included.
        self.assertNotIn("total_dref_allocation", kwargs["operational_strategy"])
        self.assertNotIn("operation_timeframe", kwargs["operational_strategy"])
        self.assertEqual(kwargs["people_centered_approach"]["people_assisted"], "6000 people")
        self.assertEqual(kwargs["people_centered_approach"]["selection_criteria"], "Vulnerable households")
        self.assertNotIn("women", kwargs["people_centered_approach"])

    def test_get_section_kwargs_for_dref_final_report(self):
        planned_intervention = PlannedInterventionFactory.create(
            challenges="Access constraints due to weather",
            lessons_learnt="Earlier pre-positioning of stock helps",
        )
        final_report = DrefFinalReportFactory.create(
            title="Test Final Report",
            event_description="Response concluded",
            operation_objective="Deliver relief items",
            response_strategy="Direct distribution",
            total_dref_allocation=150000,
            people_assisted="7000 people",
            selection_criteria="Most affected households",
            women=1200,
            men=1100,
            girls=600,
            boys=700,
            planned_interventions=[planned_intervention],
        )

        kwargs = DrefSummaryGenerator.get_section_kwargs(final_report)

        self.assertEqual(
            set(kwargs.keys()),
            {
                "situational_overview",
                "needs_identified",
                "operational_strategy",
                "people_centered_approach",
                "challenges_identified",
                "lessons_learned",
            },
        )
        self.assertEqual(kwargs["situational_overview"]["event_description"], "Response concluded")
        self.assertEqual(kwargs["operational_strategy"]["operation_objective"], "Deliver relief items")
        self.assertNotIn("total_dref_allocation", kwargs["operational_strategy"])
        self.assertNotIn("women", kwargs["people_centered_approach"])

        challenges = kwargs["challenges_identified"]["planned_interventions"]
        self.assertEqual(len(challenges), 1)
        self.assertEqual(challenges[0]["challenges"], "Access constraints due to weather")

        lessons = kwargs["lessons_learned"]["planned_interventions"]
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["lessons_learnt"], "Earlier pre-positioning of stock helps")

    def test_get_section_kwargs_drops_empty_event_scope(self):
        # event_scope is dropped only when empty (e.g. an Imminent DREF Application
        # where the scope is not yet known); a populated value always feeds the summary.
        empty_scope_dref = DrefFactory.create(type_of_dref=Dref.DrefType.IMMINENT, event_scope="")
        self.assertNotIn("event_scope", DrefSummaryGenerator.get_section_kwargs(empty_scope_dref)["situational_overview"])

        response_dref = DrefFactory.create(type_of_dref=Dref.DrefType.RESPONSE, event_scope="scope text")
        self.assertIn("event_scope", DrefSummaryGenerator.get_section_kwargs(response_dref)["situational_overview"])

    def test_get_section_kwargs_keeps_event_scope_for_imminent_final_report(self):
        # By the Final Report stage an Imminent event has materialized, so event_scope
        # (the "events impact") is real data and must feed the summary — unlike the
        # Application stage where it is not yet known.
        imminent_final = DrefFinalReportFactory.create(
            type_of_dref=Dref.DrefType.IMMINENT,
            event_scope="Two districts flooded, 5000 people displaced",
        )
        situational = DrefSummaryGenerator.get_section_kwargs(imminent_final)["situational_overview"]
        self.assertEqual(situational["event_scope"], "Two districts flooded, 5000 people displaced")

    def test_get_section_kwargs_uses_scenario_analysis_for_imminent_v2_application(self):
        # An imminent v2 application has no event yet: the situation is described in
        # hazard_date_and_location, not event_description/event_scope.
        imminent_v2 = DrefFactory.create(
            type_of_dref=Dref.DrefType.IMMINENT,
            is_dref_imminent_v2=True,
            hazard_date_and_location="Cyclone landfall expected 12-14 March in Sofala province",
            event_description="Should not be used",
            event_scope="Should not be used",
        )
        situational = DrefSummaryGenerator.get_section_kwargs(imminent_v2)["situational_overview"]
        self.assertEqual(
            situational,
            {"hazard_date_and_location": "Cyclone landfall expected 12-14 March in Sofala province"},
        )

        # The flag alone does not switch fields — an imminent DREF that is not v2, and
        # a v2 flag on any other type, both keep the common fields.
        old_imminent = DrefFactory.create(
            type_of_dref=Dref.DrefType.IMMINENT,
            hazard_date_and_location="Ignored here",
            event_description="Cyclone approaching",
        )
        self.assertEqual(
            DrefSummaryGenerator.get_section_kwargs(old_imminent)["situational_overview"]["event_description"],
            "Cyclone approaching",
        )

    def test_get_section_kwargs_for_imminent_v2_follow_up_uses_common_fields(self):
        # hazard_date_and_location lives on Dref alone, so a follow-up document of an
        # imminent v2 DREF has nothing to read it from and uses the common fields.
        dref = DrefFactory.create(
            type_of_dref=Dref.DrefType.IMMINENT,
            is_dref_imminent_v2=True,
            hazard_date_and_location="Cyclone landfall expected 12-14 March",
        )
        ops_update = DrefOperationalUpdateFactory.create(
            dref=dref,
            type_of_dref=Dref.DrefType.IMMINENT,
            event_description="Cyclone made landfall on 13 March",
        )

        situational = DrefSummaryGenerator.get_section_kwargs(ops_update)["situational_overview"]
        self.assertEqual(situational["event_description"], "Cyclone made landfall on 13 March")
        self.assertNotIn("hazard_date_and_location", situational)

    def test_compute_source_hash_changes_with_content_and_is_deterministic(self):
        dref = DrefFactory.create(event_description="Original description", type_of_dref=Dref.DrefType.RESPONSE)

        hash_a = DrefSummaryGenerator.compute_source_hash(dref)
        hash_b = DrefSummaryGenerator.compute_source_hash(dref)
        self.assertEqual(hash_a, hash_b)

        # The hash tracks the mapped source fields, so changing one must change it.
        dref.event_description = "Changed description"
        dref.save(update_fields=["event_description"])
        hash_c = DrefSummaryGenerator.compute_source_hash(dref)
        self.assertNotEqual(hash_a, hash_c)

    def test_compute_source_hash_uses_provided_section_kwargs(self):
        dref = DrefFactory.create(title="Test Dref", type_of_dref=Dref.DrefType.RESPONSE)
        default_hash = DrefSummaryGenerator.compute_source_hash(dref)

        actual_kwargs = DrefSummaryGenerator.get_section_kwargs(dref)
        self.assertEqual(default_hash, DrefSummaryGenerator.compute_source_hash(dref, section_kwargs=actual_kwargs))

        custom_kwargs = {"situational_overview": {"title": "overridden"}}
        self.assertNotEqual(default_hash, DrefSummaryGenerator.compute_source_hash(dref, section_kwargs=custom_kwargs))

    def test_get_latest_approved_source_returns_none_when_dref_not_approved(self):
        dref = DrefFactory.create(status=Dref.Status.FINALIZED)
        self.assertIsNone(DrefSummaryGenerator.get_latest_approved_source(dref))

    def test_get_latest_approved_source_follows_priority_order(self):
        dref = DrefFactory.create(status=Dref.Status.APPROVED)
        self.assertEqual(DrefSummaryGenerator.get_latest_approved_source(dref), (DrefSummary.SourceModel.DREF, dref))

        # Unapproved updates don't count, so the Dref itself still wins.
        DrefOperationalUpdateFactory.create(dref=dref, status=Dref.Status.FINALIZED, operational_update_number=1)
        self.assertEqual(DrefSummaryGenerator.get_latest_approved_source(dref), (DrefSummary.SourceModel.DREF, dref))

        # An approved Operational Update supersedes the Dref; the higher
        # operational_update_number wins, regardless of insertion order.
        DrefOperationalUpdateFactory.create(dref=dref, status=Dref.Status.APPROVED, operational_update_number=1)
        ops_update_2 = DrefOperationalUpdateFactory.create(dref=dref, status=Dref.Status.APPROVED, operational_update_number=2)
        self.assertEqual(
            DrefSummaryGenerator.get_latest_approved_source(dref),
            (DrefSummary.SourceModel.DREF_OPERATIONAL_UPDATE, ops_update_2),
        )

        # An approved Final Report supersedes everything else.
        final_report = DrefFinalReportFactory.create(dref=dref, status=Dref.Status.APPROVED)
        self.assertEqual(
            DrefSummaryGenerator.get_latest_approved_source(dref),
            (DrefSummary.SourceModel.DREF_FINAL_REPORT, final_report),
        )

    def test_returns_source_not_found_when_dref_missing_or_nothing_approved(self):
        self.assertEqual(generate_dref_summary(dref_id=999999), DrefSummaryGenerationResult.SOURCE_NOT_FOUND)

        dref = DrefFactory.create(status=Dref.Status.FINALIZED)
        self.assertEqual(generate_dref_summary(dref_id=dref.id), DrefSummaryGenerationResult.SOURCE_NOT_FOUND)

    def test_generates_from_dref_and_is_up_to_date_on_rerun(self):
        dref = DrefFactory.create(status=Dref.Status.APPROVED)

        self.assertEqual(generate_dref_summary(dref_id=dref.id), DrefSummaryGenerationResult.SUCCESS)
        summary = DrefSummary.objects.get(dref=dref)
        self.assertEqual(summary.source, DrefSummary.SourceModel.DREF)
        self.assertEqual(summary.source_id, dref.id)

        # Nothing changed since - re-running should not regenerate.
        self.assertEqual(generate_dref_summary(dref_id=dref.id), DrefSummaryGenerationResult.UP_TO_DATE)

    def test_retrigger_with_overwrite_regenerates_even_when_up_to_date(self):
        dref = DrefFactory.create(status=Dref.Status.APPROVED)

        self.assertEqual(generate_dref_summary(dref_id=dref.id), DrefSummaryGenerationResult.SUCCESS)
        summary = DrefSummary.objects.get(dref=dref)
        first_hash = summary.source_hash
        first_updated_at = summary.updated_at

        # Nothing changed since, so a plain retrigger would be UP_TO_DATE ...
        self.assertEqual(generate_dref_summary(dref_id=dref.id), DrefSummaryGenerationResult.UP_TO_DATE)

        # ... but overwrite=True must bypass that check and regenerate anyway.
        self.assertEqual(generate_dref_summary(dref_id=dref.id, overwrite=True), DrefSummaryGenerationResult.SUCCESS)

        self.assertEqual(DrefSummary.objects.filter(dref=dref).count(), 1)
        summary.refresh_from_db()
        self.assertEqual(summary.status, DrefSummary.SummaryStatus.SUCCESS)
        self.assertEqual(summary.source, DrefSummary.SourceModel.DREF)
        self.assertEqual(summary.source_id, dref.id)
        self.assertEqual(summary.source_hash, first_hash)
        self.assertGreater(summary.updated_at, first_updated_at)

    def test_processing_in_flight_skips_same_source_but_regenerates_for_a_newer_one(self):
        dref = DrefFactory.create(status=Dref.Status.APPROVED)
        # Simulate a run already in flight for the Dref itself.
        DrefSummary.objects.create(
            dref=dref,
            source=DrefSummary.SourceModel.DREF,
            source_id=dref.id,
            source_hash="in-flight-hash",
            status=DrefSummary.SummaryStatus.PROCESSING,
        )

        # A duplicate trigger for the same in-flight source is dropped.
        self.assertEqual(generate_dref_summary(dref_id=dref.id), DrefSummaryGenerationResult.ALREADY_IN_PROGRESS)

        # A newer approval lands while that run is still (supposedly) processing.
        ops_update = DrefOperationalUpdateFactory.create(dref=dref, status=Dref.Status.APPROVED, operational_update_number=1)

        self.assertEqual(generate_dref_summary(dref_id=dref.id), DrefSummaryGenerationResult.SUCCESS)
        summary = DrefSummary.objects.get(dref=dref)
        self.assertEqual(summary.source, DrefSummary.SourceModel.DREF_OPERATIONAL_UPDATE)
        self.assertEqual(summary.source_id, ops_update.id)

    def test_generate_all_succeeds_for_newer_ops_update_while_older_one_in_flight(self):
        """Two Operational Updates on one Dref: a run in flight for the older
        one must not block generation once a newer one is approved."""
        dref = DrefFactory.create(status=Dref.Status.APPROVED)
        ops_update_1 = DrefOperationalUpdateFactory.create(dref=dref, status=Dref.Status.APPROVED, operational_update_number=1)
        DrefSummary.objects.create(
            dref=dref,
            source=DrefSummary.SourceModel.DREF_OPERATIONAL_UPDATE,
            source_id=ops_update_1.id,
            source_hash="in-flight-hash",
            status=DrefSummary.SummaryStatus.PROCESSING,
        )

        # A duplicate trigger for the same in-flight source (ops_update_1) is dropped.
        self.assertEqual(generate_dref_summary(dref_id=dref.id), DrefSummaryGenerationResult.ALREADY_IN_PROGRESS)

        # A second, newer Operational Update is approved while that run is still (supposedly) processing.
        ops_update_2 = DrefOperationalUpdateFactory.create(dref=dref, status=Dref.Status.APPROVED, operational_update_number=2)

        # The in-flight record is for a now-stale source (ops_update_1), so this
        # trigger falls through and regenerates from ops_update_2 instead of
        # being blocked as "already in progress".
        self.assertEqual(generate_dref_summary(dref_id=dref.id), DrefSummaryGenerationResult.SUCCESS)

        # Exactly one DrefSummary row for the Dref - updated in place, not duplicated.
        self.assertEqual(DrefSummary.objects.filter(dref=dref).count(), 1)
        summary = DrefSummary.objects.get(dref=dref)
        self.assertEqual(summary.source, DrefSummary.SourceModel.DREF_OPERATIONAL_UPDATE)
        self.assertEqual(summary.source_id, ops_update_2.id)
        self.assertEqual(summary.status, DrefSummary.SummaryStatus.SUCCESS)
        self.assertNotEqual(summary.source_hash, "in-flight-hash")

        # Nothing changed since - re-running should not regenerate.
        self.assertEqual(generate_dref_summary(dref_id=dref.id), DrefSummaryGenerationResult.UP_TO_DATE)
