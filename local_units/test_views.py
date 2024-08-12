import datetime

import factory
from django.contrib.gis.geos import Point

from api.models import Country, Region
from deployments.factories.user import UserFactory
from main.test_case import APITestCase

from .models import (
    Affiliation,
    DelegationOffice,
    DelegationOfficeType,
    FacilityType,
    Functionality,
    LocalUnit,
    LocalUnitLevel,
    LocalUnitType,
    PrimaryHCC,
    VisibilityChoices,
)


class LocalUnitFactory(factory.django.DjangoModelFactory):
    location = Point(12, 38)
    date_of_data = factory.fuzzy.FuzzyDate(datetime.date(2024, 1, 2))

    class Meta:
        model = LocalUnit


class TestLocalUnitsListView(APITestCase):
    def setUp(self):
        super().setUp()
        region = Region.objects.create(name=2)
        country = Country.objects.create(name="Nepal", iso3="NLP", iso="NP", region=region)
        country_1 = Country.objects.create(
            name="Philippines",
            iso3="PHL",
            iso="PH",
            region=region,
        )
        type = LocalUnitType.objects.create(code=0, name="Code 0")
        type_1 = LocalUnitType.objects.create(code=1, name="Code 1")
        LocalUnitFactory.create_batch(5, country=country, type=type, draft=True, validated=False, date_of_data="2023-09-09")
        LocalUnitFactory.create_batch(5, country=country_1, type=type_1, draft=False, validated=True, date_of_data="2023-08-08")

    def test_list(self):
        self.authenticate()
        response = self.client.get("/api/v2/local-units/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 10)
        # TODO: fix these asaywltdi
        # self.assertEqual(response.data['results'][0]['location_details']['coordinates'], [12, 38])
        # self.assertEqual(response.data['results'][0]['country_details']['name'], 'Nepal')
        # self.assertEqual(response.data['results'][0]['country_details']['iso3'], 'NLP')
        # self.assertEqual(response.data['results'][0]['type_details']['name'], 'Code 0')
        # self.assertEqual(response.data['results'][0]['type_details']['code'], 0)

    def test_filter(self):
        self.authenticate()
        response = self.client.get("/api/v2/local-units/?country__name=Nepal")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/local-units/?country__name=Philippines")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/local-units/?country__name=Belgium")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

        response = self.client.get("/api/v2/local-units/?country__iso=BE")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

        response = self.client.get("/api/v2/local-units/?country__iso3=BEL")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

        response = self.client.get("/api/v2/local-units/?country__iso=BE")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

        response = self.client.get("/api/v2/local-units/?country__iso3=PHL")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/local-units/?country__iso=NP")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/local-units/?type__code=0")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/local-units/?type__code=4")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

        response = self.client.get("/api/v2/local-units/?draft=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/local-units/?draft=false")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/local-units/?validated=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/local-units/?validated=false")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)


class TestLocalUnitsDetailView(APITestCase):
    def setUp(self):
        super().setUp()
        self.region = Region.objects.create(name=2)
        self.country = Country.objects.create(name="Nepal", iso3="NLP", region=self.region)
        self.type = LocalUnitType.objects.create(code=0, name="Code 0")
        LocalUnitFactory.create_batch(2, country=self.country, type=self.type)

    def test_detail(self):
        local_unit = LocalUnit.objects.all().first()
        self.authenticate()
        response = self.client.get(f"/api/v2/local-units/{local_unit.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["location_details"]["coordinates"], [12, 38])
        self.assertEqual(response.data["country_details"]["name"], "Nepal")
        self.assertEqual(response.data["country_details"]["iso3"], "NLP")
        self.assertEqual(response.data["type_details"]["name"], "Code 0")
        self.assertEqual(response.data["type_details"]["code"], 0)

        # test for guest user
        self.user.profile.limit_access_to_guest = True
        self.user.profile.save()

        self.authenticate()
        # -- Should fail for normal view
        response = self.client.get(f"/api/v2/local-units/{local_unit.id}/")
        self.assertEqual(response.status_code, 403)

        # -- Should pass for public view
        local_unit = LocalUnitFactory.create(country=self.country, type=self.type, visibility=VisibilityChoices.PUBLIC)
        response = self.client.get(f"/api/v2/public-local-units/{local_unit.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["location_details"]["coordinates"], [12, 38])
        self.assertEqual(response.data["country_details"]["name"], "Nepal")
        self.assertEqual(response.data["country_details"]["iso3"], "NLP")
        self.assertEqual(response.data["type_details"]["name"], "Code 0")
        self.assertEqual(response.data["type_details"]["code"], 0)

    def test_get_updated_at_updated_by(self):
        self.authenticate()
        user_1 = UserFactory.create()
        user_2 = UserFactory.create()
        user_1_local_units = LocalUnitFactory.create_batch(
            2, country=self.country, type=self.type, created_by=user_1, modified_by=user_1
        )
        user_2_local_units = LocalUnitFactory.create_batch(
            2, country=self.country, type=self.type, created_by=user_1, modified_by=user_2
        )
        user_1_local_unit = LocalUnit.objects.filter(id__in=[unit.id for unit in user_1_local_units]).first()
        user_2_local_unit = LocalUnit.objects.filter(id__in=[unit.id for unit in user_2_local_units]).first()
        response = self.client.get(f"/api/v2/local-units/{user_1_local_unit.id}/")
        self.assertIsNotNone(response.data["modified_at"])
        self.assertEqual(response.data["modified_by_details"]["id"], user_1.id)

        response = self.client.get(f"/api/v2/local-units/{user_2_local_unit.id}/")
        self.assertIsNotNone(response.data["modified_at"])
        self.assertEqual(response.data["modified_by_details"]["id"], user_2.id)

    def test_validate_local_units(self):
        local_unit = LocalUnit.objects.all().first()
        self.authenticate()
        url = f"/api/v2/local-units/{local_unit.id}/validate/"
        data = {}
        response = self.client.post(url, data=data)
        self.assert_403(response)

        # authenticate with super user
        self.client.force_authenticate(self.root_user)
        response = self.client.post(url, data=data)
        self.assert_200(response)


class DelegationOfficeFactory(factory.django.DjangoModelFactory):
    location = Point(2.2, 3.3)

    class Meta:
        model = DelegationOffice


class TestDelegationOfficesListView(APITestCase):
    def setUp(self):
        region = Region.objects.create(name=2)
        country = Country.objects.create(name="Nepal", iso3="NLP", iso="NP", region=region)
        country_1 = Country.objects.create(name="Philippines", iso3="PHL", iso="PH", region=region)
        type = DelegationOfficeType.objects.create(code=0, name="Code 0")
        type_1 = DelegationOfficeType.objects.create(code=1, name="Code 1")
        DelegationOfficeFactory.create_batch(5, country=country, dotype=type)
        DelegationOfficeFactory.create_batch(5, country=country_1, dotype=type_1)

    def test_list(self):
        response = self.client.get("/api/v2/delegation-office/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 10)
        self.assertEqual(response.data["results"][0]["location"]["coordinates"], [2.2, 3.3])
        self.assertEqual(response.data["results"][0]["country"]["name"], "Nepal")
        self.assertEqual(response.data["results"][0]["country"]["iso3"], "NLP")
        self.assertEqual(response.data["results"][0]["dotype"]["name"], "Code 0")
        self.assertEqual(response.data["results"][0]["dotype"]["code"], 0)

    def test_filter(self):
        response = self.client.get("/api/v2/delegation-office/?country__name=Nepal")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/delegation-office/?country__name=Philippines")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/delegation-office/?country__name=Belgium")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

        response = self.client.get("/api/v2/delegation-office/?country__iso=BE")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

        response = self.client.get("/api/v2/delegation-office/?country__iso3=BEL")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

        response = self.client.get("/api/v2/delegation-office/?country__iso=BE")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

        response = self.client.get("/api/v2/delegation-office/?country__iso3=PHL")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/delegation-office/?country__iso=NP")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/delegation-office/?dotype__code=0")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/delegation-office/?dotype__code=4")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)


class TestDelegationOfficesDetailView(APITestCase):
    def setUp(self):
        region = Region.objects.create(name=2)
        country = Country.objects.create(name="Nepal", iso3="NLP", region=region)
        type = DelegationOfficeType.objects.create(code=0, name="Code 0")
        DelegationOfficeFactory.create_batch(2, country=country, dotype=type)

    def test_detail(self):
        local_unit = DelegationOffice.objects.all().first()
        self.authenticate()
        response = self.client.get(f"/api/v2/delegation-office/{local_unit.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["location"]["coordinates"], [2.2, 3.3])
        self.assertEqual(response.data["country"]["name"], "Nepal")
        self.assertEqual(response.data["country"]["iso3"], "NLP")
        self.assertEqual(response.data["dotype"]["name"], "Code 0")
        self.assertEqual(response.data["dotype"]["code"], 0)


class TestLocalUnitCreate(APITestCase):

    def test_create_local_unit_administrative(self):
        region = Region.objects.create(name=2)
        country = Country.objects.create(
            name="Philippines",
            iso3="PHL",
            iso="PH",
            region=region,
        )
        type = LocalUnitType.objects.create(code=1, name="Code 0")
        level = LocalUnitLevel.objects.create(level=1, name="Code 1")

        data = {
            "local_branch_name": None,
            "english_branch_name": None,
            "type": type.id,
            "country": country.id,
            "draft": False,
            "validated": True,
            "postcode": "4407",
            "address_loc": "4407",
            "address_en": "",
            "city_loc": "",
            "city_en": "Pukë",
            "link": "",
            "location_json": {
                "lat": 42.066667,
                "lng": 19.983333,
            },
            "source_loc": "",
            "source_en": "",
            "subtype": "District Office",
            "date_of_data": "2024-05-13",
            "level": level.id,
            "focal_person_loc": "Test Name",
            "focal_person_en": "Test Name",
            "email": "",
            "phone": "",
            # "health": {}
        }
        self.authenticate()
        response = self.client.post("/api/v2/local-units/", data=data, format="json")
        self.assertEqual(response.status_code, 400)

        # add `english branch_name`
        data["english_branch_name"] = "Test branch name"
        response = self.client.post("/api/v2/local-units/", data=data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_update_local_unit_health(self):
        region = Region.objects.create(name=2)
        country = Country.objects.create(name="Philippines", iso3="PHL", iso="PH", region=region)
        type = LocalUnitType.objects.create(code=2, name="Code 0")
        level = LocalUnitLevel.objects.create(level=1, name="Code 1")
        affiliation = Affiliation.objects.create(code=1, name="Code 1")
        functionality = Functionality.objects.create(code=1, name="Code 1")
        health_facility_type = FacilityType.objects.create(code=1, name="Code 1")
        primary_health_care_center = PrimaryHCC.objects.create(code=1, name="Code 1")

        data = {
            "local_branch_name": "Silele Red Cross Clinic, Sigombeni Red Cross Clinic & Mahwalala Red Cross Clinic",
            "english_branch_name": None,
            "type": type.id,
            "country": country.id,
            "created_at": "2024-05-13T06:53:14.978083Z",
            "modified_at": "2024-05-13T06:53:14.978099Z",
            "draft": False,
            "validated": True,
            "postcode": "",
            "address_loc": "Silele Clinic is is in Hosea Inkhundla under the Shiselweni, Sigombeni is in Nkom'iyahlaba Inkhundla under the Manzini region and Mahwalala is in the Mbabane West Inkhundla under the Hhohho region.",  # noqa: E501
            "address_en": "",
            "city_loc": "",
            "city_en": "",
            "link": "",
            "location": "SRID=4326;POINT (31.567837 -27.226852)",
            "source_loc": "",
            "source_en": "",
            "subtype": "",
            "date_of_data": "2024-05-13",
            "level": level.id,
            "location_json": {
                "lat": 42.066667,
                "lng": 19.983333,
            },
            "health": {
                "other_affiliation": None,
                "focal_point_email": "jele@redcross.org.sz",
                "focal_point_phone_number": "26876088546",
                "focal_point_position": "Programmes Manager",
                "other_facility_type": None,
                "speciality": "Initiate TB treatment, Cervical Cancer Screening and testing and diagnostic and treatment for people living with HIV and follow up care through the ART programme which the government supports very well",  # noqa: E501
                "is_teaching_hospital": False,
                "is_in_patient_capacity": False,
                "is_isolation_rooms_wards": False,
                "maximum_capacity": None,
                "number_of_isolation_rooms": None,
                "is_warehousing": None,
                "is_cold_chain": None,
                "ambulance_type_a": None,
                "ambulance_type_b": None,
                "ambulance_type_c": None,
                "other_services": None,
                "total_number_of_human_resource": 32,
                "general_practitioner": 0,
                "specialist": 0,
                "residents_doctor": 0,
                "nurse": 3,
                "dentist": 0,
                "nursing_aid": 0,
                "midwife": 9,
                "other_medical_heal": True,
                "other_profiles": None,
                "feedback": "first question of initial question did not provide for the option to write the name of the NS. It is written LRC yet it should allow Baphalali Eswatini Red Cross Society (BERCS) to be inscribed in the box.",  # noqa: E501
                "affiliation": affiliation.id,
                "functionality": functionality.id,
                "health_facility_type": health_facility_type.id,
                "primary_health_care_center": primary_health_care_center.id,
                "hospital_type": None,
                "general_medical_services": [1, 2, 3, 4, 5],
                "specialized_medical_beyond_primary_level": [4, 10, 22],
                "blood_services": [2],
                "professional_training_facilities": [],
            },
            "visibility_display": "RCRC Movement",
            "focal_person_loc": "Elliot Jele",
            "focal_person_en": "",
            "email": "",
            "phone": "",
        }
        self.client.force_authenticate(self.root_user)
        response = self.client.post("/api/v2/local-units/", data=data, format="json")
        self.assertEqual(response.status_code, 201)

        # test update
        response = response.json()
        local_unit_id = response["id"]
        response_updated_1 = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json").json()
        local_unit_obj = LocalUnit.objects.get(id=local_unit_id)
        self.assertIsNotNone(local_unit_obj.created_by)
        self.assertIsNotNone(response_updated_1["modified_by"])
        self.assertIsNotNone(response_updated_1["modified_at"])
        self.assertEqual(response_updated_1["modified_by"], local_unit_obj.created_by.id)

        # update existing local_unit with new user
        user_1 = UserFactory()
        self.client.force_authenticate(user_1)
        response_updated_2 = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json").json()
        self.assertEqual(response_updated_2["modified_by_details"]["id"], user_1.id)
        self.assertEqual(response_updated_2["created_by_details"]["id"], self.root_user.id)
        assert response_updated_1["modified_at"] < response_updated_2["modified_at"]
