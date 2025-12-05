import os
import tempfile
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core import management
from django.utils.translation import get_language as django_get_language

from api.factories.country import CountryFactory
from api.factories.disaster_type import DisasterTypeFactory
from api.models import Export
from deployments.factories.user import UserFactory
from eap.factories import (
    EAPFileFactory,
    EAPRegistrationFactory,
    EnableApproachFactory,
    FullEAPFactory,
    KeyActorFactory,
    OperationActivityFactory,
    PlannedOperationFactory,
    SimplifiedEAPFactory,
)
from eap.models import (
    DaysTimeFrameChoices,
    EAPFile,
    EAPStatus,
    EAPType,
    EnableApproach,
    MonthsTimeFrameChoices,
    PlannedOperation,
    SimplifiedEAP,
    TimeFrame,
    YearsTimeFrameChoices,
)
from main.test_case import APITestCase


class EAPFileTestCase(APITestCase):
    def setUp(self):
        super().setUp()

        path = os.path.join(settings.TEST_DIR, "documents")
        self.file = os.path.join(path, "go.png")

    def test_upload_file(self):
        file_count = EAPFile.objects.count()
        url = "/api/v2/eap-file/"
        data = {
            "file": open(self.file, "rb"),
        }
        self.authenticate()
        response = self.client.post(url, data, format="multipart")
        self.assert_201(response)
        self.assertEqual(EAPFile.objects.count(), file_count + 1)

    def test_upload_multiple_file(self):
        file_count = EAPFile.objects.count()
        url = "/api/v2/eap-file/multiple/"
        data = {"file": [open(self.file, "rb")]}

        self.authenticate()
        response = self.client.post(url, data, format="multipart")
        self.assert_201(response)
        self.assertEqual(EAPFile.objects.count(), file_count + 1)

    def test_upload_invalid_files(self):
        file_count = EAPFile.objects.count()
        url = "/api/v2/eap-file/multiple/"
        data = {
            "file": [
                open(self.file, "rb"),
                open(self.file, "rb"),
                open(self.file, "rb"),
                "test_string",
            ]
        }

        self.authenticate()
        response = self.client.post(url, data, format="multipart")
        self.assert_400(response)
        # no new files to be created
        self.assertEqual(EAPFile.objects.count(), file_count)


class EAPRegistrationTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.country = CountryFactory.create(name="country1", iso3="EAP", iso="EA")
        self.national_society = CountryFactory.create(
            name="national_society1",
            iso3="NSC",
            iso="NS",
        )
        self.disaster_type = DisasterTypeFactory.create(name="disaster1")
        self.partner1 = CountryFactory.create(name="partner1", iso3="ZZZ", iso="P1")
        self.partner2 = CountryFactory.create(name="partner2", iso3="AAA", iso="P2")

        # Create permissions
        management.call_command("make_permissions")

        # Create Country Admin User and assign permission
        self.country_admin = UserFactory.create()
        country_admin_permission = Permission.objects.filter(codename="country_admin_%s" % self.national_society.id).first()
        country_group = Group.objects.filter(name="%s Admins" % self.national_society.name).first()

        self.country_admin.user_permissions.add(country_admin_permission)
        self.country_admin.groups.add(country_group)

    def test_list_eap_registration(self):
        EAPRegistrationFactory.create_batch(
            5,
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            created_by=self.country_admin,
            modified_by=self.country_admin,
        )
        url = "/api/v2/eap-registration/"
        self.authenticate()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 5)

    def test_create_eap_registration(self):
        url = "/api/v2/eap-registration/"
        data = {
            "eap_type": EAPType.FULL_EAP,
            "country": self.country.id,
            "national_society": self.national_society.id,
            "disaster_type": self.disaster_type.id,
            "expected_submission_time": "2024-12-31",
            "partners": [self.partner1.id, self.partner2.id],
        }

        self.authenticate(self.country_admin)
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 201)
        # Check created_by
        self.assertIsNotNone(response.data["created_by_details"])
        self.assertEqual(
            response.data["created_by_details"]["id"],
            self.country_admin.id,
        )
        self.assertEqual(
            {
                response.data["eap_type"],
                response.data["status"],
                response.data["country"],
                response.data["disaster_type_details"]["id"],
            },
            {
                EAPType.FULL_EAP,
                EAPStatus.UNDER_DEVELOPMENT,
                self.country.id,
                self.disaster_type.id,
            },
        )

    def test_retrieve_eap_registration(self):
        eap_registration = EAPRegistrationFactory.create(
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner1.id, self.partner2.id],
            created_by=self.country_admin,
            modified_by=self.country_admin,
        )
        url = f"/api/v2/eap-registration/{eap_registration.id}/"

        self.authenticate(self.country_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], eap_registration.id)

    def test_update_eap_registration(self):
        eap_registration = EAPRegistrationFactory.create(
            country=self.country,
            eap_type=EAPType.SIMPLIFIED_EAP,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner1.id],
            created_by=self.country_admin,
            modified_by=self.country_admin,
        )
        url = f"/api/v2/eap-registration/{eap_registration.id}/"

        # Change Country and Partners
        country2 = CountryFactory.create(name="country2", iso3="BBB")
        partner3 = CountryFactory.create(name="partner3", iso3="CCC")

        data = {
            "country": country2.id,
            "national_society": self.national_society.id,
            "disaster_type": self.disaster_type.id,
            "expected_submission_time": "2025-01-15",
            "partners": [self.partner2.id, partner3.id],
        }

        # Authenticate as root user
        self.authenticate(self.root_user)
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)

        # Check modified_by
        self.assertIsNotNone(response.data["modified_by_details"])
        self.assertEqual(
            response.data["modified_by_details"]["id"],
            self.root_user.id,
        )

        # Check country and partner
        self.assertEqual(response.data["country_details"]["id"], country2.id)
        self.assertEqual(len(response.data["partners_details"]), 2)
        partner_ids = [p["id"] for p in response.data["partners_details"]]
        self.assertIn(self.partner2.id, partner_ids)

        # Check cannot update EAP Registration once application is being created
        SimplifiedEAPFactory.create(
            eap_registration=eap_registration,
            created_by=self.country_admin,
            modified_by=self.country_admin,
            budget_file=EAPFileFactory._create_file(
                created_by=self.country_admin,
                modified_by=self.country_admin,
            ),
        )

        data_update = {
            "country": self.country.id,
            "national_society": self.national_society.id,
            "disaster_type": self.disaster_type.id,
            "expected_submission_time": "2025-02-01",
            "partners": [self.partner1.id],
        }
        response = self.client.patch(url, data_update, format="json")
        self.assertEqual(response.status_code, 400)

    def test_active_eaps(self):
        eap_registration_1 = EAPRegistrationFactory.create(
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner1.id],
            created_by=self.country_admin,
            modified_by=self.country_admin,
            status=EAPStatus.APPROVED,
            eap_type=EAPType.FULL_EAP,
        )
        eap_registration_2 = EAPRegistrationFactory.create(
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner2.id],
            created_by=self.country_admin,
            modified_by=self.country_admin,
            status=EAPStatus.ACTIVATED,
            eap_type=EAPType.SIMPLIFIED_EAP,
        )
        EAPRegistrationFactory.create(
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner1.id, self.partner2.id],
            created_by=self.country_admin,
            modified_by=self.country_admin,
            status=EAPStatus.NS_ADDRESSING_COMMENTS,
        )

        EAPRegistrationFactory.create(
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner1.id, self.partner2.id],
            created_by=self.country_admin,
            modified_by=self.country_admin,
            status=EAPStatus.UNDER_REVIEW,
        )

        full_eap_1 = FullEAPFactory.create(
            eap_registration=eap_registration_1,
            total_budget=5000,
            created_by=self.country_admin,
            modified_by=self.country_admin,
            budget_file=EAPFileFactory._create_file(
                created_by=self.country_admin,
                modified_by=self.country_admin,
            ),
        )

        full_eap_snapshot_1 = FullEAPFactory.create(
            eap_registration=eap_registration_1,
            total_budget=10_000,
            created_by=self.country_admin,
            modified_by=self.country_admin,
            budget_file=EAPFileFactory._create_file(
                created_by=self.country_admin,
                modified_by=self.country_admin,
            ),
            parent_id=full_eap_1.id,
            is_locked=True,
            version=2,
        )

        full_eap_snapshot_2 = FullEAPFactory.create(
            eap_registration=eap_registration_1,
            total_budget=12_000,
            created_by=self.country_admin,
            modified_by=self.country_admin,
            budget_file=EAPFileFactory._create_file(
                created_by=self.country_admin,
                modified_by=self.country_admin,
            ),
            parent_id=full_eap_snapshot_1.id,
            is_locked=False,
            version=3,
        )

        simplifed_eap_1 = SimplifiedEAPFactory.create(
            eap_registration=eap_registration_1,
            created_by=self.country_admin,
            modified_by=self.country_admin,
            total_budget=5000,
            budget_file=EAPFileFactory._create_file(
                created_by=self.country_admin,
                modified_by=self.country_admin,
            ),
        )
        simplifed_eap_snapshot_1 = SimplifiedEAPFactory.create(
            eap_registration=eap_registration_2,
            total_budget=10_000,
            created_by=self.country_admin,
            modified_by=self.country_admin,
            budget_file=EAPFileFactory._create_file(
                created_by=self.country_admin,
                modified_by=self.country_admin,
            ),
            parent_id=simplifed_eap_1.id,
            is_locked=True,
            version=2,
        )

        simplifed_eap_snapshot_2 = SimplifiedEAPFactory.create(
            eap_registration=eap_registration_2,
            total_budget=12_000,
            created_by=self.country_admin,
            modified_by=self.country_admin,
            budget_file=EAPFileFactory._create_file(
                created_by=self.country_admin,
                modified_by=self.country_admin,
            ),
            parent_id=simplifed_eap_snapshot_1.id,
            is_locked=False,
            version=3,
        )

        url = "/api/v2/active-eap/"
        self.authenticate()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["results"]), 2, response.data["results"])

        # Check requirement_cost values
        # NOTE: it's the latest unlocked snapshot total_budget
        self.assertEqual(
            {
                response.data["results"][0]["requirement_cost"],
                response.data["results"][1]["requirement_cost"],
            },
            {
                full_eap_snapshot_2.total_budget,
                simplifed_eap_snapshot_2.total_budget,
            },
        )


class EAPSimplifiedTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.country = CountryFactory.create(name="country1", iso3="EAP", iso="EA")
        self.national_society = CountryFactory.create(
            name="national_society1",
            iso3="NSC",
            iso="NS",
        )
        self.disaster_type = DisasterTypeFactory.create(name="disaster1")
        self.partner1 = CountryFactory.create(name="partner1", iso3="ZZZ", iso="P1")
        self.partner2 = CountryFactory.create(name="partner2", iso3="AAA", iso="P2")

        # Create permissions
        management.call_command("make_permissions")

        # Create Country Admin User and assign permission
        self.country_admin = UserFactory.create()
        country_admin_permission = Permission.objects.filter(codename="country_admin_%s" % self.national_society.id).first()
        country_group = Group.objects.filter(name="%s Admins" % self.national_society.name).first()

        self.country_admin.user_permissions.add(country_admin_permission)
        self.country_admin.groups.add(country_group)

    def test_list_simplified_eap(self):
        eap_registrations = EAPRegistrationFactory.create_batch(
            5,
            eap_type=EAPType.SIMPLIFIED_EAP,
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner1.id, self.partner2.id],
            created_by=self.country_admin,
            modified_by=self.country_admin,
        )

        for eap in eap_registrations:
            SimplifiedEAPFactory.create(
                eap_registration=eap,
                created_by=self.country_admin,
                modified_by=self.country_admin,
                budget_file=EAPFileFactory._create_file(
                    created_by=self.country_admin,
                    modified_by=self.country_admin,
                ),
            )

        url = "/api/v2/simplified-eap/"
        self.authenticate()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 5)

    def test_create_simplified_eap(self):
        url = "/api/v2/simplified-eap/"
        eap_registration = EAPRegistrationFactory.create(
            eap_type=EAPType.SIMPLIFIED_EAP,
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner1.id, self.partner2.id],
            created_by=self.country_admin,
            modified_by=self.country_admin,
        )
        budget_file = EAPFileFactory._create_file(
            created_by=self.country_admin,
            modified_by=self.country_admin,
        )
        data = {
            "eap_registration": eap_registration.id,
            "prioritized_hazard_and_impact": "Floods with potential heavy impact.",
            "risks_selected_protocols": "Protocol A and Protocol B.",
            "selected_early_actions": "The early actions selected.",
            "overall_objective_intervention": "To reduce risks through early actions.",
            "potential_geographical_high_risk_areas": "Area 1, Area 2, and Area 3.",
            "trigger_threshold_justification": "Based on historical data and expert analysis.",
            "early_action_capability": "High capability with trained staff.",
            "rcrc_movement_involvement": "Involves multiple RCRC societies.",
            "assisted_through_operation": "5000",
            "budget_file": budget_file.id,
            "total_budget": 10000,
            "seap_timeframe": 3,
            "seap_lead_timeframe_unit": TimeFrame.MONTHS,
            "seap_lead_time": 6,
            "operational_timeframe_unit": TimeFrame.MONTHS,
            "operational_timeframe": 12,
            "readiness_budget": 3000,
            "pre_positioning_budget": 4000,
            "early_action_budget": 3000,
            "people_targeted": 5000,
            "next_step_towards_full_eap": "Plan to expand.",
            "planned_operations": [
                {
                    "sector": PlannedOperation.Sector.SETTLEMENT_AND_HOUSING,
                    "ap_code": 111,
                    "people_targeted": 10000,
                    "budget_per_sector": 100000,
                    "indicators": [
                        {
                            "title": "indicator 1",
                            "target": 100,
                        },
                        {
                            "title": "indicator 2",
                            "target": 200,
                        },
                    ],
                    "early_action_activities": [
                        {
                            "activity": "early action activity",
                            "timeframe": TimeFrame.YEARS,
                            "time_value": [
                                YearsTimeFrameChoices.ONE_YEAR,
                                YearsTimeFrameChoices.TWO_YEARS,
                            ],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "activity": "prepositioning activity",
                            "timeframe": TimeFrame.YEARS,
                            "time_value": [
                                YearsTimeFrameChoices.TWO_YEARS,
                                YearsTimeFrameChoices.THREE_YEARS,
                            ],
                        }
                    ],
                    "readiness_activities": [
                        {
                            "activity": "readiness activity",
                            "timeframe": TimeFrame.YEARS,
                            "time_value": [YearsTimeFrameChoices.FIVE_YEARS],
                        }
                    ],
                }
            ],
            "enable_approaches": [
                {
                    "ap_code": 11,
                    "approach": EnableApproach.Approach.SECRETARIAT_SERVICES,
                    "budget_per_approach": 10000,
                    "indicators": [
                        {
                            "title": "indicator enable approach 1",
                            "target": 100,
                        },
                        {
                            "title": "indicator enable approach 2",
                            "target": 200,
                        },
                    ],
                    "early_action_activities": [
                        {
                            "activity": "early action activity",
                            "timeframe": TimeFrame.YEARS,
                            "time_value": [
                                YearsTimeFrameChoices.TWO_YEARS,
                                YearsTimeFrameChoices.THREE_YEARS,
                            ],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "activity": "prepositioning activity",
                            "timeframe": TimeFrame.YEARS,
                            "time_value": [YearsTimeFrameChoices.THREE_YEARS],
                        }
                    ],
                    "readiness_activities": [
                        {
                            "activity": "readiness activity",
                            "timeframe": TimeFrame.YEARS,
                            "time_value": [
                                YearsTimeFrameChoices.FIVE_YEARS,
                                YearsTimeFrameChoices.TWO_YEARS,
                            ],
                        }
                    ],
                },
            ],
        }

        self.authenticate(self.country_admin)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201, response.data)

        self.assertEqual(
            response.data["eap_registration"],
            eap_registration.id,
        )
        self.assertEqual(
            eap_registration.get_eap_type_enum,
            EAPType.SIMPLIFIED_EAP,
        )

        # Cannot create Simplified EAP for the same EAP Registration again
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_update_simplified_eap(self):
        eap_registration = EAPRegistrationFactory.create(
            eap_type=EAPType.SIMPLIFIED_EAP,
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner1.id, self.partner2.id],
            created_by=self.country_admin,
            modified_by=self.country_admin,
        )
        enable_approach_readiness_operation_activity_1 = OperationActivityFactory.create(
            activity="Readiness Activity 1",
            timeframe=TimeFrame.MONTHS,
            time_value=[MonthsTimeFrameChoices.ONE_MONTH, MonthsTimeFrameChoices.TWO_MONTHS],
        )
        enable_approach_readiness_operation_activity_2 = OperationActivityFactory.create(
            activity="Readiness Activity 2",
            timeframe=TimeFrame.YEARS,
            time_value=[YearsTimeFrameChoices.ONE_YEAR, YearsTimeFrameChoices.FIVE_YEARS],
        )
        enable_approach_prepositioning_operation_activity_1 = OperationActivityFactory.create(
            activity="Prepositioning Activity 1",
            timeframe=TimeFrame.MONTHS,
            time_value=[
                MonthsTimeFrameChoices.TWO_MONTHS,
                MonthsTimeFrameChoices.FOUR_MONTHS,
            ],
        )
        enable_approach_prepositioning_operation_activity_2 = OperationActivityFactory.create(
            activity="Prepositioning Activity 2",
            timeframe=TimeFrame.MONTHS,
            time_value=[
                MonthsTimeFrameChoices.THREE_MONTHS,
                MonthsTimeFrameChoices.SIX_MONTHS,
            ],
        )
        enable_approach_early_action_operation_activity_1 = OperationActivityFactory.create(
            activity="Early Action Activity 1",
            timeframe=TimeFrame.DAYS,
            time_value=[DaysTimeFrameChoices.FIVE_DAYS, DaysTimeFrameChoices.TEN_DAYS],
        )
        enable_approach_early_action_operation_activity_2 = OperationActivityFactory.create(
            activity="Early Action Activity 2",
            timeframe=TimeFrame.MONTHS,
            time_value=[
                MonthsTimeFrameChoices.ONE_MONTH,
                MonthsTimeFrameChoices.THREE_MONTHS,
            ],
        )

        # ENABLE APPROACH with activities
        enable_approach = EnableApproachFactory.create(
            approach=EnableApproach.Approach.SECRETARIAT_SERVICES,
            budget_per_approach=5000,
            ap_code=123,
            readiness_activities=[
                enable_approach_readiness_operation_activity_1.id,
                enable_approach_readiness_operation_activity_2.id,
            ],
            prepositioning_activities=[
                enable_approach_prepositioning_operation_activity_1.id,
                enable_approach_prepositioning_operation_activity_2.id,
            ],
            early_action_activities=[
                enable_approach_early_action_operation_activity_1.id,
                enable_approach_early_action_operation_activity_2.id,
            ],
        )
        planned_operation_readiness_operation_activity_1 = OperationActivityFactory.create(
            activity="Readiness Activity 1",
            timeframe=TimeFrame.MONTHS,
            time_value=[MonthsTimeFrameChoices.ONE_MONTH, MonthsTimeFrameChoices.FOUR_MONTHS],
        )
        planned_operation_readiness_operation_activity_2 = OperationActivityFactory.create(
            activity="Readiness Activity 2",
            timeframe=TimeFrame.YEARS,
            time_value=[YearsTimeFrameChoices.ONE_YEAR, YearsTimeFrameChoices.THREE_YEARS],
        )
        planned_operation_prepositioning_operation_activity_1 = OperationActivityFactory.create(
            activity="Prepositioning Activity 1",
            timeframe=TimeFrame.MONTHS,
            time_value=[
                MonthsTimeFrameChoices.TWO_MONTHS,
                MonthsTimeFrameChoices.FOUR_MONTHS,
            ],
        )
        planned_operation_prepositioning_operation_activity_2 = OperationActivityFactory.create(
            activity="Prepositioning Activity 2",
            timeframe=TimeFrame.MONTHS,
            time_value=[
                MonthsTimeFrameChoices.THREE_MONTHS,
                MonthsTimeFrameChoices.SIX_MONTHS,
            ],
        )
        planned_operation_early_action_operation_activity_1 = OperationActivityFactory.create(
            activity="Early Action Activity 1",
            timeframe=TimeFrame.DAYS,
            time_value=[DaysTimeFrameChoices.FIVE_DAYS, DaysTimeFrameChoices.TEN_DAYS],
        )
        planned_operation_early_action_operation_activity_2 = OperationActivityFactory.create(
            activity="Early Action Activity 2",
            timeframe=TimeFrame.MONTHS,
            time_value=[
                MonthsTimeFrameChoices.ONE_MONTH,
                MonthsTimeFrameChoices.THREE_MONTHS,
            ],
        )

        # PLANNED OPERATION with activities
        planned_operation = PlannedOperationFactory.create(
            sector=PlannedOperation.Sector.SHELTER,
            ap_code=456,
            people_targeted=5000,
            budget_per_sector=50000,
            readiness_activities=[
                planned_operation_readiness_operation_activity_1.id,
                planned_operation_readiness_operation_activity_2.id,
            ],
            prepositioning_activities=[
                planned_operation_prepositioning_operation_activity_1.id,
                planned_operation_prepositioning_operation_activity_2.id,
            ],
            early_action_activities=[
                planned_operation_early_action_operation_activity_1.id,
                planned_operation_early_action_operation_activity_2.id,
            ],
        )

        simplified_eap = SimplifiedEAPFactory.create(
            eap_registration=eap_registration,
            created_by=self.country_admin,
            modified_by=self.country_admin,
            seap_lead_timeframe_unit=TimeFrame.MONTHS,
            seap_lead_time=12,
            operational_timeframe=12,
            operational_timeframe_unit=TimeFrame.MONTHS,
            budget_file=EAPFileFactory._create_file(
                created_by=self.country_admin,
                modified_by=self.country_admin,
            ),
            enable_approaches=[enable_approach.id],
            planned_operations=[planned_operation.id],
        )
        url = f"/api/v2/simplified-eap/{simplified_eap.id}/"

        data = {
            "eap_registration": eap_registration.id,
            "total_budget": 20000,
            "readiness_budget": 8000,
            "pre_positioning_budget": 7000,
            "early_action_budget": 5000,
            "enable_approaches": [
                {
                    "id": enable_approach.id,
                    "approach": EnableApproach.Approach.NATIONAL_SOCIETY_STRENGTHENING,
                    "budget_per_approach": 8000,
                    "ap_code": 123,
                    "readiness_activities": [
                        {
                            "id": enable_approach_readiness_operation_activity_1.id,
                            "activity": "Updated Enable Approach Readiness Activity 1",
                            "timeframe": TimeFrame.MONTHS,
                            "time_value": [MonthsTimeFrameChoices.TWO_MONTHS],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "id": enable_approach_prepositioning_operation_activity_1.id,
                            "activity": "Updated Enable Approach Prepositioning Activity 1",
                            "timeframe": TimeFrame.MONTHS,
                            "time_value": [MonthsTimeFrameChoices.FOUR_MONTHS],
                        }
                    ],
                    "early_action_activities": [
                        {
                            "id": enable_approach_early_action_operation_activity_1.id,
                            "activity": "Updated Enable Approach Early Action Activity 1",
                            "timeframe": TimeFrame.DAYS,
                            "time_value": [DaysTimeFrameChoices.TEN_DAYS],
                        }
                    ],
                },
                # CREATE NEW Enable Approach
                {
                    "approach": EnableApproach.Approach.PARTNERSHIP_AND_COORDINATION,
                    "budget_per_approach": 9000,
                    "ap_code": 124,
                    "readiness_activities": [
                        {
                            "activity": "New Enable Approach Readiness Activity",
                            "timeframe": TimeFrame.MONTHS,
                            "time_value": [
                                MonthsTimeFrameChoices.THREE_MONTHS,
                                MonthsTimeFrameChoices.SIX_MONTHS,
                            ],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "activity": "New Enable Approach Prepositioning Activity",
                            "timeframe": TimeFrame.MONTHS,
                            "time_value": [
                                MonthsTimeFrameChoices.SIX_MONTHS,
                                MonthsTimeFrameChoices.NINE_MONTHS,
                            ],
                        }
                    ],
                    "early_action_activities": [
                        {
                            "activity": "New Enable Approach Early Action Activity",
                            "timeframe": TimeFrame.DAYS,
                            "time_value": [
                                DaysTimeFrameChoices.EIGHT_DAYS,
                                DaysTimeFrameChoices.SIXTEEN_DAYS,
                            ],
                        }
                    ],
                },
            ],
            "planned_operations": [
                {
                    "id": planned_operation.id,
                    "sector": PlannedOperation.Sector.SHELTER,
                    "ap_code": 456,
                    "people_targeted": 8000,
                    "budget_per_sector": 80000,
                    "indicators": [
                        {
                            "title": "indicator 1",
                            "target": 100,
                        },
                        {
                            "title": "indicator 2",
                            "target": 200,
                        },
                    ],
                    "readiness_activities": [
                        {
                            "id": planned_operation_readiness_operation_activity_1.id,
                            "activity": "Updated Planned Operation Readiness Activity 1",
                            "timeframe": TimeFrame.MONTHS,
                            "time_value": [
                                MonthsTimeFrameChoices.TWO_MONTHS,
                                MonthsTimeFrameChoices.SIX_MONTHS,
                            ],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "id": planned_operation_prepositioning_operation_activity_1.id,
                            "activity": "Updated Planned Operation Prepositioning Activity 1",
                            "timeframe": TimeFrame.MONTHS,
                            "time_value": [
                                MonthsTimeFrameChoices.THREE_MONTHS,
                                MonthsTimeFrameChoices.SIX_MONTHS,
                            ],
                        }
                    ],
                    "early_action_activities": [
                        {
                            "id": planned_operation_early_action_operation_activity_1.id,
                            "activity": "Updated Planned Operation Early Action Activity 1",
                            "timeframe": TimeFrame.DAYS,
                            "time_value": [
                                DaysTimeFrameChoices.EIGHT_DAYS,
                                DaysTimeFrameChoices.SIXTEEN_DAYS,
                            ],
                        }
                    ],
                },
                {
                    # CREATE NEW Planned OperationActivity
                    "sector": PlannedOperation.Sector.HEALTH_AND_CARE,
                    "ap_code": 457,
                    "people_targeted": 6000,
                    "budget_per_sector": 60000,
                    "readiness_activities": [
                        {
                            "activity": "New Planned Operation Readiness Activity",
                            "timeframe": TimeFrame.MONTHS,
                            "time_value": [
                                MonthsTimeFrameChoices.THREE_MONTHS,
                                MonthsTimeFrameChoices.SIX_MONTHS,
                            ],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "activity": "New Planned Operation Prepositioning Activity",
                            "timeframe": TimeFrame.MONTHS,
                            "time_value": [
                                MonthsTimeFrameChoices.TWO_MONTHS,
                                MonthsTimeFrameChoices.FIVE_MONTHS,
                            ],
                        }
                    ],
                    "early_action_activities": [
                        {
                            "activity": "New Planned Operation Early Action Activity",
                            "timeframe": TimeFrame.DAYS,
                            "time_value": [
                                MonthsTimeFrameChoices.FIVE_MONTHS,
                                MonthsTimeFrameChoices.TWELVE_MONTHS,
                            ],
                        }
                    ],
                },
            ],
        }

        # Authenticate as root user
        self.authenticate(self.root_user)
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["eap_registration"],
            eap_registration.id,
        )

        # Check modified_by
        self.assertIsNotNone(response.data["modified_by_details"])
        self.assertEqual(
            response.data["modified_by_details"]["id"],
            self.root_user.id,
        )

        # CHECK ENABLE APPROACH UPDATED
        self.assertEqual(len(response.data["enable_approaches"]), 2)
        self.assertEqual(
            {
                response.data["enable_approaches"][0]["id"],
                response.data["enable_approaches"][0]["approach"],
                response.data["enable_approaches"][0]["budget_per_approach"],
                response.data["enable_approaches"][0]["ap_code"],
                # NEW DATA
                response.data["enable_approaches"][1]["approach"],
                response.data["enable_approaches"][1]["budget_per_approach"],
                response.data["enable_approaches"][1]["ap_code"],
            },
            {
                enable_approach.id,
                data["enable_approaches"][0]["approach"],
                data["enable_approaches"][0]["budget_per_approach"],
                data["enable_approaches"][0]["ap_code"],
                # NEW DATA
                data["enable_approaches"][1]["approach"],
                data["enable_approaches"][1]["budget_per_approach"],
                data["enable_approaches"][1]["ap_code"],
            },
        )
        self.assertEqual(
            {
                # READINESS ACTIVITY
                response.data["enable_approaches"][0]["readiness_activities"][0]["id"],
                response.data["enable_approaches"][0]["readiness_activities"][0]["activity"],
                response.data["enable_approaches"][0]["readiness_activities"][0]["timeframe"],
                # NEW READINESS ACTIVITY
                response.data["enable_approaches"][1]["readiness_activities"][0]["activity"],
                response.data["enable_approaches"][1]["readiness_activities"][0]["timeframe"],
                # PREPOSITIONING ACTIVITY
                response.data["enable_approaches"][0]["prepositioning_activities"][0]["id"],
                response.data["enable_approaches"][0]["prepositioning_activities"][0]["activity"],
                response.data["enable_approaches"][0]["prepositioning_activities"][0]["timeframe"],
                # NEW PREPOSITIONING ACTIVITY
                response.data["enable_approaches"][1]["prepositioning_activities"][0]["activity"],
                response.data["enable_approaches"][1]["prepositioning_activities"][0]["timeframe"],
                # EARLY ACTION ACTIVITY
                response.data["enable_approaches"][0]["early_action_activities"][0]["id"],
                response.data["enable_approaches"][0]["early_action_activities"][0]["activity"],
                response.data["enable_approaches"][0]["early_action_activities"][0]["timeframe"],
                # NEW EARLY ACTION ACTIVITY
                response.data["enable_approaches"][1]["early_action_activities"][0]["activity"],
                response.data["enable_approaches"][1]["early_action_activities"][0]["timeframe"],
            },
            {
                # READINESS ACTIVITY
                enable_approach_readiness_operation_activity_1.id,
                data["enable_approaches"][0]["readiness_activities"][0]["activity"],
                data["enable_approaches"][0]["readiness_activities"][0]["timeframe"],
                # NEW READINESS ACTIVITY
                data["enable_approaches"][1]["readiness_activities"][0]["activity"],
                data["enable_approaches"][1]["readiness_activities"][0]["timeframe"],
                # PREPOSITIONING ACTIVITY
                enable_approach_prepositioning_operation_activity_1.id,
                data["enable_approaches"][0]["prepositioning_activities"][0]["activity"],
                data["enable_approaches"][0]["prepositioning_activities"][0]["timeframe"],
                # NEW PREPOSITIONING Activity
                data["enable_approaches"][1]["prepositioning_activities"][0]["activity"],
                data["enable_approaches"][1]["prepositioning_activities"][0]["timeframe"],
                # EARLY ACTION ACTIVITY
                enable_approach_early_action_operation_activity_1.id,
                data["enable_approaches"][0]["early_action_activities"][0]["activity"],
                data["enable_approaches"][0]["early_action_activities"][0]["timeframe"],
                # NEW EARLY ACTION ACTIVITY
                data["enable_approaches"][1]["early_action_activities"][0]["activity"],
                data["enable_approaches"][1]["early_action_activities"][0]["timeframe"],
            },
        )

        # CHECK PLANNED OPERATION UPDATED
        self.assertEqual(len(response.data["planned_operations"]), 2)
        self.assertEqual(
            {
                response.data["planned_operations"][0]["id"],
                response.data["planned_operations"][0]["sector"],
                response.data["planned_operations"][0]["ap_code"],
                response.data["planned_operations"][0]["people_targeted"],
                response.data["planned_operations"][0]["budget_per_sector"],
                # NEW DATA
                response.data["planned_operations"][1]["sector"],
                response.data["planned_operations"][1]["ap_code"],
                response.data["planned_operations"][1]["people_targeted"],
                response.data["planned_operations"][1]["budget_per_sector"],
            },
            {
                planned_operation.id,
                data["planned_operations"][0]["sector"],
                data["planned_operations"][0]["ap_code"],
                data["planned_operations"][0]["people_targeted"],
                data["planned_operations"][0]["budget_per_sector"],
                # NEW DATA
                data["planned_operations"][1]["sector"],
                data["planned_operations"][1]["ap_code"],
                data["planned_operations"][1]["people_targeted"],
                data["planned_operations"][1]["budget_per_sector"],
            },
        )

        self.assertEqual(
            {
                # READINESS ACTIVITY
                response.data["planned_operations"][0]["readiness_activities"][0]["id"],
                response.data["planned_operations"][0]["readiness_activities"][0]["activity"],
                response.data["planned_operations"][0]["readiness_activities"][0]["timeframe"],
                # NEW READINESS ACTIVITY
                response.data["planned_operations"][1]["readiness_activities"][0]["activity"],
                response.data["planned_operations"][1]["readiness_activities"][0]["timeframe"],
                # PREPOSITIONING ACTIVITY
                response.data["planned_operations"][0]["prepositioning_activities"][0]["id"],
                response.data["planned_operations"][0]["prepositioning_activities"][0]["activity"],
                response.data["planned_operations"][0]["prepositioning_activities"][0]["timeframe"],
                # NEW PREPOSITIONING ACTIVITY
                response.data["planned_operations"][1]["prepositioning_activities"][0]["activity"],
                response.data["planned_operations"][1]["prepositioning_activities"][0]["timeframe"],
                # EARLY ACTION ACTIVITY
                response.data["planned_operations"][0]["early_action_activities"][0]["id"],
                response.data["planned_operations"][0]["early_action_activities"][0]["activity"],
                response.data["planned_operations"][0]["early_action_activities"][0]["timeframe"],
                # NEW EARLY ACTION ACTIVITY
                response.data["planned_operations"][1]["early_action_activities"][0]["activity"],
                response.data["planned_operations"][1]["early_action_activities"][0]["timeframe"],
            },
            {
                # READINESS ACTIVITY
                planned_operation_readiness_operation_activity_1.id,
                data["planned_operations"][0]["readiness_activities"][0]["activity"],
                data["planned_operations"][0]["readiness_activities"][0]["timeframe"],
                # NEW READINESS ACTIVITY
                data["planned_operations"][1]["readiness_activities"][0]["activity"],
                data["planned_operations"][1]["readiness_activities"][0]["timeframe"],
                # PREPOSITIONING ACTIVITY
                planned_operation_prepositioning_operation_activity_1.id,
                data["planned_operations"][0]["prepositioning_activities"][0]["activity"],
                data["planned_operations"][0]["prepositioning_activities"][0]["timeframe"],
                # NEW PREPOSITIONING ACTIVITY
                data["planned_operations"][1]["prepositioning_activities"][0]["activity"],
                data["planned_operations"][1]["prepositioning_activities"][0]["timeframe"],
                # EARLY ACTION Activity
                planned_operation_early_action_operation_activity_1.id,
                data["planned_operations"][0]["early_action_activities"][0]["activity"],
                data["planned_operations"][0]["early_action_activities"][0]["timeframe"],
                # NEW EARLY ACTION Activity
                data["planned_operations"][1]["early_action_activities"][0]["activity"],
                data["planned_operations"][1]["early_action_activities"][0]["timeframe"],
            },
        )


class EAPStatusTransitionTestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.country = CountryFactory.create(name="country1", iso3="EAP", iso="EA")
        self.national_society = CountryFactory.create(
            name="national_society1",
            iso3="NSC",
            iso="NS",
        )
        self.disaster_type = DisasterTypeFactory.create(name="disaster1")
        self.partner1 = CountryFactory.create(name="partner1", iso3="ZZZ", iso="ZZ")
        self.partner2 = CountryFactory.create(name="partner2", iso3="AAA", iso="AA")

        self.eap_registration = EAPRegistrationFactory.create(
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            eap_type=EAPType.SIMPLIFIED_EAP,
            status=EAPStatus.UNDER_DEVELOPMENT,
            partners=[self.partner1.id, self.partner2.id],
            created_by=self.user,
            modified_by=self.user,
        )
        self.url = f"/api/v2/eap-registration/{self.eap_registration.id}/status/"

    # TODO(susilnem): Update test case for file uploads once implemented
    def test_status_transition(self):
        # Create permissions
        management.call_command("make_permissions")

        # Create Country Admin User and assign permission
        self.country_admin = UserFactory.create()
        country_admin_permission = Permission.objects.filter(codename="country_admin_%s" % self.national_society.id).first()
        country_group = Group.objects.filter(name="%s Admins" % self.national_society.name).first()

        self.country_admin.user_permissions.add(country_admin_permission)
        self.country_admin.groups.add(country_group)

        # Create IFRC Admin User and assign permission
        self.ifrc_admin_user = UserFactory.create()
        ifrc_admin_permission = Permission.objects.filter(codename="ifrc_admin").first()
        ifrc_group = Group.objects.filter(name="IFRC Admins").first()
        self.ifrc_admin_user.user_permissions.add(ifrc_admin_permission)
        self.ifrc_admin_user.groups.add(ifrc_group)

        # NOTE: Transition to UNDER REVIEW
        # UNDER_DEVELOPMENT -> UNDER_REVIEW
        data = {
            "status": EAPStatus.UNDER_REVIEW,
        }
        self.authenticate()

        # FAILS: As User is not country admin or IFRC admin or superuser
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)

        # Authenticate as country admin user
        self.authenticate(self.country_admin)

        # FAILS: As no Simplified or Full EAP created yet
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)

        simplified_eap = SimplifiedEAPFactory.create(
            eap_registration=self.eap_registration,
            created_by=self.country_admin,
            modified_by=self.country_admin,
            budget_file=EAPFileFactory._create_file(
                created_by=self.country_admin,
                modified_by=self.country_admin,
            ),
        )

        # SUCCESS: As Simplified EAP exists
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], EAPStatus.UNDER_REVIEW)

        # NOTE: Transition to NS_ADDRESSING_COMMENTS
        # UNDER_REVIEW -> NS_ADDRESSING_COMMENTS
        data = {
            "status": EAPStatus.NS_ADDRESSING_COMMENTS,
        }

        # FAILS: As country admin cannot
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)

        # NOTE: Login as IFRC admin user
        # FAILS: As review_checklist_file is required
        self.authenticate(self.ifrc_admin_user)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)

        # Uploading review checklist file
        # Create a temporary .xlsx file for testing
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmp_file:
            tmp_file.write(b"Test content")
            tmp_file.seek(0)

            data["review_checklist_file"] = tmp_file

            response = self.client.post(self.url, data, format="multipart")
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["status"], EAPStatus.NS_ADDRESSING_COMMENTS)

            self.eap_registration.refresh_from_db()
            self.assertIsNotNone(
                self.eap_registration.review_checklist_file,
            )

            # NOTE: Check if snapshot is created or not
            # First SimplifedEAP should be locked
            simplified_eap.refresh_from_db()
            self.assertTrue(simplified_eap.is_locked)

            # Two SimplifiedEAP should be there
            eap_simplified_queryset = SimplifiedEAP.objects.filter(
                eap_registration=self.eap_registration,
            )

            self.assertEqual(
                eap_simplified_queryset.count(),
                2,
                "There should be two snapshots created.",
            )

            # Check version of the latest snapshot
            # Version should be 2
            second_snapshot = eap_simplified_queryset.order_by("-version").first()
            assert second_snapshot is not None, "Second snapshot should not be None."

            self.assertEqual(
                second_snapshot.version,
                2,
                "Latest snapshot version should be 2.",
            )
            # Check for parent_id
            self.assertEqual(
                second_snapshot.parent_id,
                simplified_eap.id,
                "Latest snapshot's parent_id should be the first SimplifiedEAP id.",
            )
            # Snapshot Shouldn't have the updated checklist file
            self.assertFalse(
                second_snapshot.updated_checklist_file.name,
                "Latest Snapshot shouldn't have the updated checklist file.",
            )

        # NOTE: Transition to UNDER_REVIEW
        # NS_ADDRESSING_COMMENTS -> UNDER_REVIEW
        data = {
            "status": EAPStatus.UNDER_REVIEW,
        }

        # FAILS: As updated checklist file is required to go back to UNDER_REVIEW
        self.authenticate(self.country_admin)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)

        # Upload updated checklist file
        # UPDATES on the second snapshot
        url = f"/api/v2/simplified-eap/{second_snapshot.id}/"
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmp_file:
            tmp_file.write(b"Updated Test content")
            tmp_file.seek(0)

            file_data = {"eap_registration": second_snapshot.eap_registration_id, "updated_checklist_file": tmp_file}

            response = self.client.patch(url, file_data, format="multipart")
            self.assertEqual(response.status_code, 200, response.data)

        # SUCCESS:
        self.authenticate(self.country_admin)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], EAPStatus.UNDER_REVIEW)

        # AGAIN NOTE: Transition to NS_ADDRESSING_COMMENTS
        # UNDER_REVIEW -> NS_ADDRESSING_COMMENTS
        data = {
            "status": EAPStatus.NS_ADDRESSING_COMMENTS,
        }

        # SUCCESS: As only ifrc admins or superuser can
        self.authenticate(self.ifrc_admin_user)

        # Uploading checklist file
        # Create a temporary .xlsx file for testing
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmp_file:
            tmp_file.write(b"Test content")
            tmp_file.seek(0)

            data["review_checklist_file"] = tmp_file

            response = self.client.post(self.url, data, format="multipart")
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["status"], EAPStatus.NS_ADDRESSING_COMMENTS)

            # Check if three snapshots are created now
            eap_simplified_queryset = SimplifiedEAP.objects.filter(
                eap_registration=self.eap_registration,
            )
            self.assertEqual(
                eap_simplified_queryset.count(),
                3,
                "There should be three snapshots created.",
            )

            # Check version of the latest snapshot
            # Version should be 2
            third_snapshot = eap_simplified_queryset.order_by("-version").first()
            assert third_snapshot is not None, "Third snapshot should not be None."

            self.assertEqual(
                third_snapshot.version,
                3,
                "Latest snapshot version should be 2.",
            )
            # Check for parent_id
            self.assertEqual(
                third_snapshot.parent_id,
                second_snapshot.id,
                "Latest snapshot's parent_id should be the second Snapshot id.",
            )

            # Check if the second snapshot is locked.
            second_snapshot.refresh_from_db()
            self.assertTrue(second_snapshot.is_locked)
            # Snapshot Shouldn't have the updated checklist file
            self.assertFalse(
                third_snapshot.updated_checklist_file.name,
                "Latest snapshot shouldn't have the updated checklist file.",
            )

        # NOTE: Again Transition to UNDER_REVIEW
        # NS_ADDRESSING_COMMENTS -> UNDER_REVIEW
        data = {
            "status": EAPStatus.UNDER_REVIEW,
        }

        # Upload updated checklist file
        # UPDATES on the second snapshot
        url = f"/api/v2/simplified-eap/{third_snapshot.id}/"
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmp_file:
            tmp_file.write(b"Updated Test content")
            tmp_file.seek(0)

            file_data = {"eap_registration": third_snapshot.eap_registration_id, "updated_checklist_file": tmp_file}

            response = self.client.patch(url, file_data, format="multipart")
            self.assertEqual(response.status_code, 200)

        # SUCCESS:
        self.authenticate(self.country_admin)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], EAPStatus.UNDER_REVIEW)

        # NOTE: Transition to TECHNICALLY_VALIDATED
        # UNDER_REVIEW -> TECHNICALLY_VALIDATED
        data = {
            "status": EAPStatus.TECHNICALLY_VALIDATED,
        }

        # Login as NS user
        # FAILS: As only ifrc admins or superuser can
        self.authenticate(self.country_admin)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)

        # Login as IFRC admin user
        # SUCCESS: As only ifrc admins or superuser can
        self.authenticate(self.ifrc_admin_user)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], EAPStatus.TECHNICALLY_VALIDATED)
        self.eap_registration.refresh_from_db()
        self.assertIsNotNone(
            self.eap_registration.technically_validated_at,
        )

        # NOTE: Transition to APPROVED
        # TECHNICALLY_VALIDATED -> APPROVED
        data = {
            "status": EAPStatus.APPROVED,
        }

        # LOGIN as country admin user
        # FAILS: As only ifrc admins or superuser can
        self.authenticate(self.country_admin)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)

        # NOTE: Upload Validated budget file
        url = f"/api/v2/eap-registration/{self.eap_registration.id}/upload-validated-budget-file/"
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmp_file:
            tmp_file.write(b"Test content")
            tmp_file.seek(0)
            file_data = {"validated_budget_file": tmp_file}
            self.authenticate(self.ifrc_admin_user)
            response = self.client.post(url, file_data, format="multipart")
            self.assertEqual(response.status_code, 200, response.data)

        self.eap_registration.refresh_from_db()
        self.assertIsNotNone(
            self.eap_registration.validated_budget_file,
        )

        # LOGIN as IFRC admin user
        # SUCCESS: As only ifrc admins or superuser can
        self.assertIsNone(self.eap_registration.approved_at)
        self.authenticate(self.ifrc_admin_user)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], EAPStatus.APPROVED)
        # Check is the approved timeline is added
        self.eap_registration.refresh_from_db()
        self.assertIsNotNone(self.eap_registration.approved_at)

        # NOTE: Transition to PFA_SIGNED
        # APPROVED -> PFA_SIGNED
        data = {
            "status": EAPStatus.PFA_SIGNED,
        }

        # LOGIN as country admin user
        # FAILS: As only ifrc admins or superuser can
        self.authenticate(self.country_admin)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)

        # LOGIN as IFRC admin user
        # SUCCESS: As only ifrc admins or superuser can
        self.assertIsNone(self.eap_registration.activated_at)
        self.authenticate(self.ifrc_admin_user)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], EAPStatus.PFA_SIGNED)
        # Check is the pfa_signed timeline is added
        self.eap_registration.refresh_from_db()
        self.assertIsNotNone(self.eap_registration.pfa_signed_at)

        # NOTE: Transition to ACTIVATED
        # PFA_SIGNED -> ACTIVATED
        data = {
            "status": EAPStatus.ACTIVATED,
        }

        # LOGIN as country admin user
        # FAILS: As only ifrc admins or superuser can
        self.authenticate(self.country_admin)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 400)

        # LOGIN as IFRC admin user
        # SUCCESS: As only ifrc admins or superuser can
        self.assertIsNone(self.eap_registration.activated_at)
        self.authenticate(self.ifrc_admin_user)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], EAPStatus.ACTIVATED)
        # Check is the activated timeline is added
        self.eap_registration.refresh_from_db()
        self.assertIsNotNone(self.eap_registration.activated_at)


class EAPPDFExportTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.country = CountryFactory.create(
            name="country1",
            iso3="EAP",
            iso="EA",
        )
        self.national_society = CountryFactory.create(
            name="national_society1",
            iso3="NSC",
            iso="NS",
        )
        self.disaster_type = DisasterTypeFactory.create(name="disaster1")
        self.partner1 = CountryFactory.create(name="partner1", iso3="ZZZ", iso="ZZ")
        self.partner2 = CountryFactory.create(name="partner2", iso3="AAA", iso="AA")

        self.user = UserFactory.create()

        self.eap_registration = EAPRegistrationFactory.create(
            eap_type=EAPType.SIMPLIFIED_EAP,
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner1.id, self.partner2.id],
            created_by=self.user,
            modified_by=self.user,
        )

        self.url = "/api/v2/pdf-export/"

    @mock.patch("api.serializers.generate_url.delay")
    def test_simplified_eap_export(self, mock_generate_url):
        self.simplified_eap = SimplifiedEAPFactory.create(
            eap_registration=self.eap_registration,
            created_by=self.user,
            modified_by=self.user,
            national_society_contact_title="NS Title Example",
            budget_file=EAPFileFactory._create_file(
                created_by=self.user,
                modified_by=self.user,
            ),
        )
        data = {
            "export_type": Export.ExportType.SIMPLIFIED_EAP,
            "export_id": self.simplified_eap.id,
            "is_pga": False,
        }

        self.authenticate(self.user)

        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post(self.url, data, format="json")
        self.assert_201(response)
        self.assertIsNotNone(response.data["id"], response.data)

        expected_url = f"{settings.GO_WEB_INTERNAL_URL}/{Export.ExportType.SIMPLIFIED_EAP}/{self.simplified_eap.id}/export/"
        self.assertEqual(response.data["url"], expected_url)
        self.assertEqual(response.data["status"], Export.ExportStatus.PENDING)

        self.assertEqual(mock_generate_url.called, True)
        title = f"{self.national_society.name}-{self.disaster_type.name}"
        mock_generate_url.assert_called_once_with(
            expected_url,
            response.data["id"],
            self.user.id,
            title,
            django_get_language(),
        )

    @mock.patch("api.serializers.generate_url.delay")
    def test_full_eap_export(self, mock_generate_url):
        self.full_eap = FullEAPFactory.create(
            eap_registration=self.eap_registration,
            created_by=self.user,
            modified_by=self.user,
            budget_file=EAPFileFactory._create_file(
                created_by=self.user,
                modified_by=self.user,
            ),
        )
        data = {
            "export_type": Export.ExportType.FULL_EAP,
            "export_id": self.full_eap.id,
            "is_pga": False,
        }

        self.authenticate(self.user)

        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post(self.url, data, format="json")
        self.assert_201(response)
        self.assertIsNotNone(response.data["id"], response.data)
        expected_url = f"{settings.GO_WEB_INTERNAL_URL}/{Export.ExportType.FULL_EAP}/{self.full_eap.id}/export/"
        self.assertEqual(response.data["url"], expected_url)
        self.assertEqual(response.data["status"], Export.ExportStatus.PENDING)

        self.assertEqual(mock_generate_url.called, True)
        title = f"{self.national_society.name}-{self.disaster_type.name}"
        mock_generate_url.assert_called_once_with(
            expected_url,
            response.data["id"],
            self.user.id,
            title,
            django_get_language(),
        )


class EAPFullTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.country = CountryFactory.create(name="country1", iso3="EAP")
        self.national_society = CountryFactory.create(
            name="national_society1",
            iso3="NSC",
        )
        self.disaster_type = DisasterTypeFactory.create(name="disaster1")

        # Create permissions
        management.call_command("make_permissions")

        # Create Country Admin User and assign permission
        self.country_admin = UserFactory.create()
        country_admin_permission = Permission.objects.filter(codename="country_admin_%s" % self.national_society.id).first()
        country_group = Group.objects.filter(name="%s Admins" % self.national_society.name).first()

        self.country_admin.user_permissions.add(country_admin_permission)
        self.country_admin.groups.add(country_group)

    def test_list_full_eap(self):
        # Create EAP Registrations
        eap_registrations = EAPRegistrationFactory.create_batch(
            5,
            eap_type=EAPType.FULL_EAP,
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            created_by=self.country_admin,
            modified_by=self.country_admin,
        )

        for eap in eap_registrations:
            FullEAPFactory.create(
                eap_registration=eap,
                created_by=self.country_admin,
                modified_by=self.country_admin,
                budget_file=EAPFileFactory._create_file(
                    created_by=self.user,
                    modified_by=self.user,
                ),
            )

        url = "/api/v2/full-eap/"
        self.authenticate()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["results"]), 5)

    def test_create_full_eap(self):
        url = "/api/v2/full-eap/"

        # Create EAP Registration
        eap_registration = EAPRegistrationFactory.create(
            eap_type=EAPType.FULL_EAP,
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            created_by=self.country_admin,
            modified_by=self.country_admin,
        )

        budget_file_instance = EAPFileFactory._create_file(
            created_by=self.country_admin,
            modified_by=self.country_admin,
        )
        data = {
            "eap_registration": eap_registration.id,
            "budget_file": budget_file_instance.id,
            "total_budget": 10000,
            "objective": "FUll eap objective",
            "lead_time": 5,
            "seap_timeframe": 5,
            "readiness_budget": 3000,
            "pre_positioning_budget": 4000,
            "early_action_budget": 3000,
            "people_targeted": 5000,
            "key_actors": [
                {
                    "national_society": self.national_society.id,
                    "description": "Key actor 1 description",
                },
                {
                    "national_society": self.country.id,
                    "description": "Key actor 1 description",
                },
            ],
            "is_worked_with_government": True,
            "worked_with_government_description": "Worked with government description",
            "is_technical_working_groups": True,
            "technical_working_group_title": "Technical working group title",
            "technical_working_groups_in_place_description": "Technical working groups in place description",
            "hazard_selection": "Flood",
            "exposed_element_and_vulnerability_factor": "Exposed elements and vulnerability factors",
            "prioritized_impact": "Prioritized impacts",
            "trigger_statement": "Triggering statement",
            "forecast_selection": "Rainfall forecast",
            "definition_and_justification_impact_level": "Definition and justification of impact levels",
            "identification_of_the_intervention_area": "Identification of the intervention areas",
            "selection_area": "Selection of the area",
            "early_action_selection_process": "Early action selection process",
            "evidence_base": "Evidence base",
            "usefulness_of_actions": "Usefulness of actions",
            "feasibility": "Feasibility text",
            "early_action_implementation_process": "Early action implementation process",
            "trigger_activation_system": "Trigger activation system",
            "selection_of_target_population": "Selection of target population",
            "stop_mechanism": "Stop mechanism",
            "meal": "meal description",
            "operational_administrative_capacity": "Operational and administrative capacity",
            "strategies_and_plans": "Strategies and plans",
            "advance_financial_capacity": "Advance financial capacity",
            # BUDGET DETAILS
            "budget_description": "Budget description",
            "readiness_cost_description": "Readiness cost description",
            "prepositioning_cost_description": "Prepositioning cost description",
            "early_action_cost_description": "Early action cost description",
            "eap_endorsement": "EAP endorsement text",
            "planned_operations": [
                {
                    "sector": PlannedOperation.Sector.SETTLEMENT_AND_HOUSING,
                    "ap_code": 111,
                    "people_targeted": 10000,
                    "budget_per_sector": 100000,
                    "indicators": [
                        {
                            "title": "indicator 1",
                            "target": 100,
                        },
                        {
                            "title": "indicator 2",
                            "target": 200,
                        },
                    ],
                    "early_action_activities": [
                        {
                            "activity": "early action activity",
                            "timeframe": TimeFrame.YEARS,
                            "time_value": [
                                YearsTimeFrameChoices.ONE_YEAR,
                                YearsTimeFrameChoices.TWO_YEARS,
                            ],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "activity": "prepositioning activity",
                            "timeframe": TimeFrame.YEARS,
                            "time_value": [
                                YearsTimeFrameChoices.TWO_YEARS,
                                YearsTimeFrameChoices.THREE_YEARS,
                            ],
                        }
                    ],
                    "readiness_activities": [
                        {
                            "activity": "readiness activity",
                            "timeframe": TimeFrame.YEARS,
                            "time_value": [YearsTimeFrameChoices.FIVE_YEARS],
                        }
                    ],
                }
            ],
            "enable_approaches": [
                {
                    "ap_code": 11,
                    "approach": EnableApproach.Approach.SECRETARIAT_SERVICES,
                    "budget_per_approach": 10000,
                    "indicators": [
                        {
                            "title": "indicator enable approach 1",
                            "target": 300,
                        },
                        {
                            "title": "indicator enable approach 2",
                            "target": 400,
                        },
                    ],
                    "early_action_activities": [
                        {
                            "activity": "early action activity",
                            "timeframe": TimeFrame.YEARS,
                            "time_value": [
                                YearsTimeFrameChoices.TWO_YEARS,
                                YearsTimeFrameChoices.THREE_YEARS,
                            ],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "activity": "prepositioning activity",
                            "timeframe": TimeFrame.YEARS,
                            "time_value": [YearsTimeFrameChoices.THREE_YEARS],
                        }
                    ],
                    "readiness_activities": [
                        {
                            "activity": "readiness activity",
                            "timeframe": TimeFrame.YEARS,
                            "time_value": [
                                YearsTimeFrameChoices.FIVE_YEARS,
                                YearsTimeFrameChoices.TWO_YEARS,
                            ],
                        }
                    ],
                },
            ],
        }

        self.authenticate(self.country_admin)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201, response.data)

        self.assertEqual(
            response.data["eap_registration"],
            eap_registration.id,
        )
        self.assertEqual(
            eap_registration.get_eap_type_enum,
            EAPType.FULL_EAP,
        )
        self.assertFalse(
            response.data["is_locked"],
            "Newly created Full EAP should not be locked.",
        )

        # Cannot create Full EAP for the same EAP Registration again
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400, response.data)

    def test_update_full_eap(self):
        # Create EAP Registration
        eap_registration = EAPRegistrationFactory.create(
            eap_type=EAPType.FULL_EAP,
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            created_by=self.country_admin,
            modified_by=self.country_admin,
        )

        full_eap = FullEAPFactory.create(
            eap_registration=eap_registration,
            created_by=self.country_admin,
            modified_by=self.country_admin,
            budget_file=EAPFileFactory._create_file(
                created_by=self.country_admin,
                modified_by=self.country_admin,
            ),
        )

        url = f"/api/v2/full-eap/{full_eap.id}/"
        data = {
            "total_budget": 20000,
            "seap_timeframe": 5,
            "key_actors": [
                {
                    "national_society": self.national_society.id,
                    "description": "Key actor 1 description",
                },
                {
                    "national_society": self.country.id,
                    "description": "Key actor 1 description",
                },
            ],
        }
        self.authenticate(self.root_user)
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 200, response.data)

        self.assertIsNotNone(response.data["modified_by_details"])
        self.assertEqual(
            {
                response.data["total_budget"],
                response.data["modified_by_details"]["id"],
            },
            {
                data["total_budget"],
                self.root_user.id,
            },
        )


class TestSnapshotEAP(APITestCase):
    def setUp(self):
        super().setUp()
        self.country = CountryFactory.create(name="country1", iso3="EAP")
        self.national_society = CountryFactory.create(
            name="national_society1",
            iso3="NSC",
        )
        self.disaster_type = DisasterTypeFactory.create(name="disaster1")
        self.user = UserFactory.create()
        self.registration = EAPRegistrationFactory.create(
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            created_by=self.user,
            modified_by=self.user,
        )

    def test_snapshot_full_eap(self):
        # Create M2M objects
        enable_approach = EnableApproachFactory.create(
            approach=EnableApproach.Approach.SECRETARIAT_SERVICES,
            budget_per_approach=5000,
            ap_code=123,
        )
        hazard_selection_image_1 = EAPFileFactory._create_file(
            created_by=self.user,
            modified_by=self.user,
        )
        hazard_selection_image_2 = EAPFileFactory._create_file(
            created_by=self.user,
            modified_by=self.user,
        )
        key_actor_1 = KeyActorFactory.create(
            national_society=self.national_society,
            description="Key actor 1 description",
        )

        key_actor_2 = KeyActorFactory.create(
            national_society=self.country,
            description="Key actor 1 description",
        )

        planned_operation = PlannedOperationFactory.create(
            sector=PlannedOperation.Sector.SHELTER,
            ap_code=456,
            people_targeted=5000,
            budget_per_sector=50000,
            readiness_activities=[
                OperationActivityFactory.create(
                    activity="Activity 1",
                    timeframe=TimeFrame.MONTHS,
                    time_value=[MonthsTimeFrameChoices.ONE_MONTH, MonthsTimeFrameChoices.FOUR_MONTHS],
                ).id,
            ],
            prepositioning_activities=[
                OperationActivityFactory.create(
                    activity="Activity 2",
                    timeframe=TimeFrame.MONTHS,
                    time_value=[MonthsTimeFrameChoices.TWO_MONTHS],
                ).id,
            ],
        )

        # Base instance
        original = FullEAPFactory.create(
            eap_registration=self.registration,
            total_budget=5000,
            budget_file=EAPFileFactory._create_file(
                created_by=self.user,
                modified_by=self.user,
            ),
            created_by=self.user,
            modified_by=self.user,
        )
        original.key_actors.add(key_actor_1, key_actor_2)
        original.enable_approaches.add(enable_approach)
        original.planned_operations.add(planned_operation)
        original.hazard_selection_images.add(hazard_selection_image_1, hazard_selection_image_2)

        # Generate snapshot
        snapshot = original.generate_snapshot()

        # PK changed
        self.assertNotEqual(snapshot.pk, original.pk)

        # Check version
        self.assertEqual(snapshot.version, original.version + 1)

        # Fields copied
        self.assertEqual(
            {
                snapshot.total_budget,
                snapshot.eap_registration,
                snapshot.created_by,
                snapshot.modified_by,
                snapshot.budget_file,
            },
            {
                original.total_budget,
                original.eap_registration,
                original.created_by,
                original.modified_by,
                original.budget_file,
            },
        )

        # M2M deeply cloned on approach
        orig_approaches = list(original.enable_approaches.all())
        snapshot_approaches = list(snapshot.enable_approaches.all())
        self.assertEqual(len(orig_approaches), len(snapshot_approaches))

        self.assertNotEqual(orig_approaches[0].pk, snapshot)

        # M2M planned operations deeply cloned
        orig_operations = list(original.planned_operations.all())
        snapshot_operations = list(snapshot.planned_operations.all())
        self.assertEqual(len(orig_operations), len(snapshot_operations))
        self.assertNotEqual(orig_operations[0].pk, snapshot_operations[0].pk)

        self.assertEqual(
            orig_operations[0].sector,
            snapshot_operations[0].sector,
        )

        # M2M operation activities deeply cloned
        orig_readiness_activities = list(orig_operations[0].readiness_activities.all())
        snapshot_readiness_activities = list(snapshot_operations[0].readiness_activities.all())
        self.assertEqual(len(orig_readiness_activities), len(snapshot_readiness_activities))

        self.assertNotEqual(
            orig_readiness_activities[0].pk,
            snapshot_readiness_activities[0].pk,
        )
        self.assertEqual(
            orig_readiness_activities[0].activity,
            snapshot_readiness_activities[0].activity,
        )

        # M2M hazard selection images copied
        orig_hazard_images = list(original.hazard_selection_images.all())
        snapshot_hazard_images = list(snapshot.hazard_selection_images.all())
        self.assertEqual(len(orig_hazard_images), len(snapshot_hazard_images))
        self.assertEqual(
            orig_hazard_images[0].pk,
            snapshot_hazard_images[0].pk,
        )
        # M2M Actors clone but not the national society FK
        orig_actors = list(original.key_actors.all())
        snapshot_actors = list(snapshot.key_actors.all())
        self.assertEqual(len(orig_actors), len(snapshot_actors))
        self.assertNotEqual(orig_actors[0].pk, snapshot_actors[0].pk)
        self.assertEqual(
            orig_actors[0].national_society,
            snapshot_actors[0].national_society,
        )
        self.assertEqual(
            orig_actors[0].description,
            snapshot_actors[0].description,
        )
