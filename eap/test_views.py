from api.factories.country import CountryFactory
from api.factories.disaster_type import DisasterTypeFactory
from eap.factories import EAPRegistrationFactory, SimplifiedEAPFactory
from eap.models import EAPStatus, EAPType
from main.test_case import APITestCase


class EAPRegistrationTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.country = CountryFactory.create(name="country1", iso3="XX")
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
        self.assertEqual(response.data["eap_type"], EAPType.FULL_EAP)
        self.assertEqual(response.data["status"], EAPStatus.UNDER_DEVELOPMENT)
        # Check created_by
        self.assertIsNotNone(response.data["created_by_details"])
        self.assertEqual(
            response.data["created_by_details"]["id"],
            self.user.id,
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


class EAPSimplifiedTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.country = CountryFactory.create(name="country1", iso3="XX")
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
        }

        self.authenticate()
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 201)

    def test_update_simplified_eap(self):
        eap_registration = EAPRegistrationFactory.create(
            country=self.country,
            national_society=self.national_society,
            disaster_type=self.disaster_type,
            partners=[self.partner1.id, self.partner2.id],
            created_by=self.user,
            modified_by=self.user,
        )
        simplified_eap = SimplifiedEAPFactory.create(
            eap_registration=eap_registration,
            created_by=self.user,
            modified_by=self.user,
        )
        url = f"/api/v2/simplified-eap/{simplified_eap.id}/"

        data = {
            "eap_registration": eap_registration.id,
            "total_budget": 20000,
            "seap_timeframe": 4,
            "readiness_budget": 8000,
            "pre_positioning_budget": 7000,
            "early_action_budget": 5000,
         }

        # Authenticate as root user
        self.authenticate(self.root_user)
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["eap_registration_details"]["id"],
            self.eap_registration.id,
        )

        # Check modified_by
        self.assertIsNotNone(response.data["modified_by_details"])
        self.assertEqual(
            response.data["modified_by_details"]["id"],
            self.root_user.id,
        )
