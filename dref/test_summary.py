from datetime import date

from django.test import TestCase, override_settings

from dref.factories.dref import (
    DrefFactory,
    DrefFinalReportFactory,
    DrefOperationalUpdateFactory,
    PlannedInterventionFactory,
)
from dref.models import Dref, DrefSummary
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
        AZURE_OPENAI_KEY="fake-key",
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
        )

        kwargs = DrefSummaryGenerator.get_section_kwargs(dref)

        self.assertEqual(set(kwargs.keys()), {"situational_overview", "operational_strategy", "people_centered_approach"})
        self.assertEqual(kwargs["situational_overview"]["title"], "Test Dref")
        self.assertEqual(kwargs["situational_overview"]["event_description"], "Severe flooding")
        self.assertEqual(kwargs["situational_overview"]["event_scope"], "Affected 3 districts")
        self.assertEqual(kwargs["operational_strategy"]["operation_objective"], "Provide shelter")
        self.assertEqual(kwargs["operational_strategy"]["response_strategy"], "Cash and shelter support")
        self.assertEqual(kwargs["operational_strategy"]["total_targeted_population"], 5000)
        self.assertEqual(kwargs["operational_strategy"]["people_in_need"], 8000)
        self.assertEqual(kwargs["people_centered_approach"]["people_assisted"], "5000 people")
        self.assertEqual(kwargs["people_centered_approach"]["selection_criteria"], "Most vulnerable households")
        self.assertNotIn("women", kwargs["people_centered_approach"])

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
        )

        kwargs = DrefSummaryGenerator.get_section_kwargs(ops_update)

        self.assertEqual(set(kwargs.keys()), {"situational_overview", "operational_strategy", "people_centered_approach"})
        self.assertEqual(kwargs["situational_overview"]["title"], "Test Ops Update")
        self.assertEqual(kwargs["situational_overview"]["event_description"], "Flooding continues")
        self.assertEqual(kwargs["operational_strategy"]["operation_objective"], "Extend shelter support")
        self.assertEqual(kwargs["operational_strategy"]["total_dref_allocation"], 100000)
        self.assertEqual(kwargs["operational_strategy"]["operation_end_date"], date(2025, 6, 1))
        self.assertEqual(kwargs["operational_strategy"]["operation_timeframe"], 6)
        self.assertEqual(kwargs["people_centered_approach"]["people_assisted"], "6000 people")
        self.assertEqual(kwargs["people_centered_approach"]["women"], 1000)
        self.assertEqual(kwargs["people_centered_approach"]["men"], 900)
        self.assertEqual(kwargs["people_centered_approach"]["girls"], 500)
        self.assertEqual(kwargs["people_centered_approach"]["boys"], 600)

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
                "operational_strategy",
                "people_centered_approach",
                "challenges_identified",
                "lessons_learned",
            },
        )
        self.assertEqual(kwargs["situational_overview"]["title"], "Test Final Report")
        self.assertEqual(kwargs["operational_strategy"]["total_dref_allocation"], 150000)
        self.assertEqual(kwargs["people_centered_approach"]["women"], 1200)

        challenges = kwargs["challenges_identified"]["planned_interventions"]
        self.assertEqual(len(challenges), 1)
        self.assertEqual(challenges[0]["challenges"], "Access constraints due to weather")

        lessons = kwargs["lessons_learned"]["planned_interventions"]
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["lessons_learnt"], "Earlier pre-positioning of stock helps")

    def test_get_section_kwargs_excludes_event_scope_for_imminent_dref(self):
        imminent_dref = DrefFactory.create(type_of_dref=Dref.DrefType.IMMINENT, event_scope="scope text")
        self.assertNotIn("event_scope", DrefSummaryGenerator.get_section_kwargs(imminent_dref)["situational_overview"])

        response_dref = DrefFactory.create(type_of_dref=Dref.DrefType.RESPONSE, event_scope="scope text")
        self.assertIn("event_scope", DrefSummaryGenerator.get_section_kwargs(response_dref)["situational_overview"])

    def test_compute_source_hash_changes_with_content_and_is_deterministic(self):
        dref = DrefFactory.create(title="Original Title", type_of_dref=Dref.DrefType.RESPONSE)

        hash_a = DrefSummaryGenerator.compute_source_hash(dref)
        hash_b = DrefSummaryGenerator.compute_source_hash(dref)
        self.assertEqual(hash_a, hash_b)

        dref.title = "Changed Title"
        dref.save(update_fields=["title"])
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
