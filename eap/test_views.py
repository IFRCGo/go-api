import os

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core import management

from api.factories.country import CountryFactory
from api.factories.disaster_type import DisasterTypeFactory
from deployments.factories.user import UserFactory
from eap.factories import (
    EAPRegistrationFactory,
    EnableApproachFactory,
    OperationActivityFactory,
    PlannedOperationFactory,
    SimplifiedEAPFactory,
)
from eap.models import (
    EAPFile,
    EAPStatus,
    EAPType,
    EnableApproach,
    OperationActivity,
    PlannedOperation,
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
        self.country = CountryFactory.create(name="country1", iso3="XXX")
        self.national_society = CountryFactory.create(
            name="national_society1",
            iso3="YYY",
        )
        self.disaster_type = DisasterTypeFactory.create(name="disaster1")
        self.partner1 = CountryFactory.create(name="partner1", iso3="ZZZ")
        self.partner2 = CountryFactory.create(name="partner2", iso3="AAA")

    def test_list_eap_registration(self):
        EAPRegistrationFactory.create_batch(
            5,
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            created_by=self.user,
            modified_by=self.user,
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

        self.authenticate()
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 201)
        # Check created_by
        self.assertIsNotNone(response.data["created_by_details"])
        self.assertEqual(
            response.data["created_by_details"]["id"],
            self.user.id,
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
            created_by=self.user,
            modified_by=self.user,
        )
        url = f"/api/v2/eap-registration/{eap_registration.id}/"

        self.authenticate()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], eap_registration.id)

    def test_update_eap_registration(self):
        eap_registration = EAPRegistrationFactory.create(
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner1.id],
            created_by=self.user,
            modified_by=self.user,
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
            created_by=self.user,
            modified_by=self.user,
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


class EAPSimplifiedTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.country = CountryFactory.create(name="country1", iso3="XXX")
        self.national_society = CountryFactory.create(
            name="national_society1",
            iso3="YYY",
        )
        self.disaster_type = DisasterTypeFactory.create(name="disaster1")
        self.partner1 = CountryFactory.create(name="partner1", iso3="ZZZ")
        self.partner2 = CountryFactory.create(name="partner2", iso3="AAA")

    def test_list_simplified_eap(self):
        eap_registrations = EAPRegistrationFactory.create_batch(
            5,
            eap_type=EAPType.SIMPLIFIED_EAP,
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner1.id, self.partner2.id],
            created_by=self.user,
            modified_by=self.user,
        )

        for eap in eap_registrations:
            SimplifiedEAPFactory.create(
                eap_registration=eap,
                created_by=self.user,
                modified_by=self.user,
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
            created_by=self.user,
            modified_by=self.user,
        )
        data = {
            "eap_registration": eap_registration.id,
            "total_budget": 10000,
            "seap_timeframe": 3,
            "readiness_budget": 3000,
            "pre_positioning_budget": 4000,
            "early_action_budget": 3000,
            "next_step_towards_full_eap": "Plan to expand.",
            "planned_operations": [
                {
                    "sector": 101,
                    "ap_code": 111,
                    "people_targeted": 10000,
                    "budget_per_sector": 100000,
                    "early_action_activities": [
                        {
                            "activity": "early action activity",
                            "timeframe": OperationActivity.TimeFrame.YEARS,
                            "time_value": [2, 3],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "activity": "prepositioning activity",
                            "timeframe": OperationActivity.TimeFrame.YEARS,
                            "time_value": [2, 3],
                        }
                    ],
                    "readiness_activities": [
                        {
                            "activity": "readiness activity",
                            "timeframe": OperationActivity.TimeFrame.YEARS,
                            "time_value": [2147483647],
                        }
                    ],
                }
            ],
            "enable_approaches": [
                {
                    "ap_code": 11,
                    "approach": 10,
                    "budget_per_approach": 10000,
                    "indicator_target": 10000,
                    "early_action_activities": [
                        {
                            "activity": "early action activity",
                            "timeframe": OperationActivity.TimeFrame.YEARS,
                            "time_value": [2, 3],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "activity": "prepositioning activity",
                            "timeframe": OperationActivity.TimeFrame.YEARS,
                            "time_value": [2, 3],
                        }
                    ],
                    "readiness_activities": [
                        {
                            "activity": "readiness activity",
                            "timeframe": OperationActivity.TimeFrame.YEARS,
                            "time_value": [2147483647],
                        }
                    ],
                },
            ],
        }

        self.authenticate()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)

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
            created_by=self.user,
            modified_by=self.user,
        )
        enable_approach_readiness_operation_activity_1 = OperationActivityFactory.create(
            activity="Readiness Activity 1",
            timeframe=OperationActivity.TimeFrame.MONTHS,
            time_value=[1, 2],
        )
        enable_approach_readiness_operation_activity_2 = OperationActivityFactory.create(
            activity="Readiness Activity 2",
            timeframe=OperationActivity.TimeFrame.YEARS,
            time_value=[1, 5],
        )
        enable_approach_prepositioning_operation_activity_1 = OperationActivityFactory.create(
            activity="Prepositioning Activity 1",
            timeframe=OperationActivity.TimeFrame.MONTHS,
            time_value=[2, 4],
        )
        enable_approach_prepositioning_operation_activity_2 = OperationActivityFactory.create(
            activity="Prepositioning Activity 2",
            timeframe=OperationActivity.TimeFrame.MONTHS,
            time_value=[3, 6],
        )
        enable_approach_early_action_operation_activity_1 = OperationActivityFactory.create(
            activity="Early Action Activity 1",
            timeframe=OperationActivity.TimeFrame.DAYS,
            time_value=[5, 10],
        )
        enable_approach_early_action_operation_activity_2 = OperationActivityFactory.create(
            activity="Early Action Activity 2",
            timeframe=OperationActivity.TimeFrame.MONTHS,
            time_value=[1, 3],
        )

        # ENABLE APPROACH with activities
        enable_approach = EnableApproachFactory.create(
            approach=EnableApproach.Approach.SECRETARIAT_SERVICES,
            budget_per_approach=5000,
            ap_code=123,
            indicator_target=500,
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
            timeframe=OperationActivity.TimeFrame.MONTHS,
            time_value=[1, 2],
        )
        planned_operation_readiness_operation_activity_2 = OperationActivityFactory.create(
            activity="Readiness Activity 2",
            timeframe=OperationActivity.TimeFrame.YEARS,
            time_value=[1, 5],
        )
        planned_operation_prepositioning_operation_activity_1 = OperationActivityFactory.create(
            activity="Prepositioning Activity 1",
            timeframe=OperationActivity.TimeFrame.MONTHS,
            time_value=[2, 4],
        )
        planned_operation_prepositioning_operation_activity_2 = OperationActivityFactory.create(
            activity="Prepositioning Activity 2",
            timeframe=OperationActivity.TimeFrame.MONTHS,
            time_value=[3, 6],
        )
        planned_operation_early_action_operation_activity_1 = OperationActivityFactory.create(
            activity="Early Action Activity 1",
            timeframe=OperationActivity.TimeFrame.DAYS,
            time_value=[5, 10],
        )
        planned_operation_early_action_operation_activity_2 = OperationActivityFactory.create(
            activity="Early Action Activity 2",
            timeframe=OperationActivity.TimeFrame.MONTHS,
            time_value=[1, 3],
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
            created_by=self.user,
            modified_by=self.user,
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
                    "indicator_target": 800,
                    "readiness_activities": [
                        {
                            "id": enable_approach_readiness_operation_activity_1.id,
                            "activity": "Updated Enable Approach Readiness Activity 1",
                            "timeframe": OperationActivity.TimeFrame.MONTHS,
                            "time_value": [2, 3],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "id": enable_approach_prepositioning_operation_activity_1.id,
                            "activity": "Updated Enable Approach Prepositioning Activity 1",
                            "timeframe": OperationActivity.TimeFrame.MONTHS,
                            "time_value": [3, 5],
                        }
                    ],
                    "early_action_activities": [
                        {
                            "id": enable_approach_early_action_operation_activity_1.id,
                            "activity": "Updated Enable Approach Early Action Activity 1",
                            "timeframe": OperationActivity.TimeFrame.DAYS,
                            "time_value": [7, 14],
                        }
                    ],
                },
                # CREATE NEW Enable Approach
                {
                    "approach": EnableApproach.Approach.PARTNERSHIP_AND_COORDINATION,
                    "budget_per_approach": 9000,
                    "ap_code": 124,
                    "indicator_target": 900,
                    "readiness_activities": [
                        {
                            "activity": "New Enable Approach Readiness Activity",
                            "timeframe": OperationActivity.TimeFrame.MONTHS,
                            "time_value": [1, 2],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "activity": "New Enable Approach Prepositioning Activity",
                            "timeframe": OperationActivity.TimeFrame.MONTHS,
                            "time_value": [2, 4],
                        }
                    ],
                    "early_action_activities": [
                        {
                            "activity": "New Enable Approach Early Action Activity",
                            "timeframe": OperationActivity.TimeFrame.DAYS,
                            "time_value": [5, 10],
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
                    "readiness_activities": [
                        {
                            "id": planned_operation_readiness_operation_activity_1.id,
                            "activity": "Updated Planned Operation Readiness Activity 1",
                            "timeframe": OperationActivity.TimeFrame.MONTHS,
                            "time_value": [2, 4],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "id": planned_operation_prepositioning_operation_activity_1.id,
                            "activity": "Updated Planned Operation Prepositioning Activity 1",
                            "timeframe": OperationActivity.TimeFrame.MONTHS,
                            "time_value": [3, 6],
                        }
                    ],
                    "early_action_activities": [
                        {
                            "id": planned_operation_early_action_operation_activity_1.id,
                            "activity": "Updated Planned Operation Early Action Activity 1",
                            "timeframe": OperationActivity.TimeFrame.DAYS,
                            "time_value": [8, 16],
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
                            "timeframe": OperationActivity.TimeFrame.MONTHS,
                            "time_value": [1, 3],
                        }
                    ],
                    "prepositioning_activities": [
                        {
                            "activity": "New Planned Operation Prepositioning Activity",
                            "timeframe": OperationActivity.TimeFrame.MONTHS,
                            "time_value": [2, 5],
                        }
                    ],
                    "early_action_activities": [
                        {
                            "activity": "New Planned Operation Early Action Activity",
                            "timeframe": OperationActivity.TimeFrame.DAYS,
                            "time_value": [5, 12],
                        }
                    ],
                },
            ],
        }

        # Authenticate as root user
        self.authenticate(self.root_user)
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 200)
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
                response.data["enable_approaches"][0]["indicator_target"],
                # NEW DATA
                response.data["enable_approaches"][1]["approach"],
                response.data["enable_approaches"][1]["budget_per_approach"],
                response.data["enable_approaches"][1]["ap_code"],
                response.data["enable_approaches"][1]["indicator_target"],
            },
            {
                enable_approach.id,
                data["enable_approaches"][0]["approach"],
                data["enable_approaches"][0]["budget_per_approach"],
                data["enable_approaches"][0]["ap_code"],
                data["enable_approaches"][0]["indicator_target"],
                # NEW DATA
                data["enable_approaches"][1]["approach"],
                data["enable_approaches"][1]["budget_per_approach"],
                data["enable_approaches"][1]["ap_code"],
                data["enable_approaches"][1]["indicator_target"],
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

        self.country = CountryFactory.create(name="country1", iso3="XXX")
        self.national_society = CountryFactory.create(
            name="national_society1",
            iso3="YYY",
        )
        self.disaster_type = DisasterTypeFactory.create(name="disaster1")
        self.partner1 = CountryFactory.create(name="partner1", iso3="ZZZ")
        self.partner2 = CountryFactory.create(name="partner2", iso3="AAA")

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

        SimplifiedEAPFactory.create(
            eap_registration=self.eap_registration,
            created_by=self.user,
            modified_by=self.user,
        )

        # SUCCESS: As Simplified EAP exists
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200)
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
        # SUCCESS: As only ifrc admins or superuser can
        self.authenticate(self.ifrc_admin_user)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], EAPStatus.NS_ADDRESSING_COMMENTS)

        # NOTE: Transition to TECHNICALLY_VALIDATED
        # NS_ADDRESSING_COMMENTS -> TECHNICALLY_VALIDATED
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

        # LOGIN as IFRC admin user
        # SUCCESS: As only ifrc admins or superuser can
        self.authenticate(self.ifrc_admin_user)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], EAPStatus.APPROVED)

        # NOTE: Transition to ACTIVATED
        # APPROVED -> ACTIVATED
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
        self.authenticate(self.ifrc_admin_user)
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], EAPStatus.ACTIVATED)
