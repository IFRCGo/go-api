import datetime

import factory
from django.contrib.auth.models import Group, Permission
from django.contrib.gis.geos import Point
from django.core import management
from factory import fuzzy

from api.factories.country import CountryFactory
from api.models import Country, CountryType, Region
from deployments.factories.user import UserFactory
from main.test_case import APITestCase

from .models import (
    Affiliation,
    DelegationOffice,
    DelegationOfficeType,
    ExternallyManagedLocalUnit,
    FacilityType,
    Functionality,
    HealthData,
    LocalUnit,
    LocalUnitChangeRequest,
    LocalUnitLevel,
    LocalUnitType,
    PrimaryHCC,
    Validator,
    VisibilityChoices,
)


class LocalUnitFactory(factory.django.DjangoModelFactory):
    location = Point(12, 38)
    date_of_data = fuzzy.FuzzyDate(datetime.date(2024, 1, 2))

    class Meta:
        model = LocalUnit


class HealthDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HealthData


class ExternallyManagedLocalUnitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExternallyManagedLocalUnit


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

    def test_deprecate_local_unit(self):
        country = Country.objects.all().first()
        type = LocalUnitType.objects.all().first()
        local_unit_obj = LocalUnitFactory.create(
            country=country, type=type, draft=True, validated=False, date_of_data="2023-09-09"
        )

        self.authenticate()
        url = f"/api/v2/local-units/{local_unit_obj.id}/deprecate/"
        data = {
            "deprecated_reason": LocalUnit.DeprecateReason.INCORRECTLY_ADDED,
            "deprecated_reason_overview": "test reason",
        }
        response = self.client.post(url, data=data)
        local_unit_obj = LocalUnit.objects.get(id=local_unit_obj.id)

        self.assert_200(response)
        self.assertEqual(local_unit_obj.is_deprecated, True)
        self.assertEqual(local_unit_obj.deprecated_reason, LocalUnit.DeprecateReason.INCORRECTLY_ADDED)

        # Test for validation
        response = self.client.post(url, data=data)
        self.assert_404(response)

        self.client.force_authenticate(self.root_user)
        # test revert deprecate
        data = {}
        url = f"/api/v2/local-units/{local_unit_obj.id}/revert-deprecate/"
        response = self.client.post(url, data=data)
        local_unit_obj = LocalUnit.objects.get(id=local_unit_obj.id)
        self.assert_200(response)
        self.assertEqual(local_unit_obj.is_deprecated, False)
        self.assertEqual(local_unit_obj.deprecated_reason, None)
        self.assertEqual(local_unit_obj.deprecated_reason_overview, "")

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
        self.assertEqual(response.data["location_geojson"]["coordinates"], [12, 38])
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
        self.assertEqual(response.data["location_geojson"]["coordinates"], [12, 38])
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

    def setUp(self):
        super().setUp()
        self.region = Region.objects.create(name=2)
        self.country = Country.objects.create(name="Nepal", iso3="NLP", region=self.region)
        management.call_command("make_permissions")
        management.call_command("make_global_validator_permission")

        # Permissions and different validators
        self.global_validator_user = UserFactory.create()
        self.local_unit_admin_user = UserFactory.create()
        self.regional_validator_user = UserFactory.create()

        # Adding permissions to the users
        global_validator_permission = Permission.objects.filter(codename="local_unit_global_validator").first()

        country_group = Group.objects.filter(name="%s Admins" % self.country.name).first()
        region_group = Group.objects.filter(name="%s Regional Admins" % self.region.name).first()

        self.local_unit_admin_user.groups.add(country_group)
        self.regional_validator_user.groups.add(region_group)

        self.global_validator_user.user_permissions.add(global_validator_permission)

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
        self.assertEqual(LocalUnitChangeRequest.objects.count(), 0)

        # add `english branch_name`
        data["english_branch_name"] = "Test branch name"
        response = self.client.post("/api/v2/local-units/", data=data, format="json")
        self.assertEqual(response.status_code, 201)

        # Checking the request changes for the local unit is created or not
        request_change = LocalUnitChangeRequest.objects.all()
        self.assertEqual(request_change.count(), 1)

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
        self.assertEqual(LocalUnitChangeRequest.objects.count(), 1)
        self.assertEqual(response.data["is_locked"], True)

        # Locked local unit should not be updated, until it is unlocked
        local_unit_id = response.data["id"]
        response = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json")
        self.assert_400(response)

        # validating the local unit
        self.client.force_authenticate(self.root_user)
        response = self.client.post(f"/api/v2/local-units/{local_unit_id}/validate/")
        self.assert_200(response)

        # Update existing local_unit with new user
        response_updated_1 = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json")
        self.assert_200(response_updated_1)

        local_unit_obj = LocalUnit.objects.get(id=local_unit_id)
        self.assertEqual(local_unit_obj.is_locked, True)
        self.assertIsNotNone(local_unit_obj.created_by)
        self.assertIsNotNone(response_updated_1.data["modified_by"])
        self.assertIsNotNone(response_updated_1.data["modified_at"])
        self.assertEqual(response_updated_1.data["modified_by"], local_unit_obj.created_by.id)

    def test_revert_local_unit(self):
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
                "residents_doctor": 0,
                "feedback": "first question of initial question did not provide for the option to write the name of the NS. It is written LRC yet it should allow Baphalali Eswatini Red Cross Society (BERCS) to be inscribed in the box.",  # noqa: E501
                "affiliation": affiliation.id,
                "functionality": functionality.id,
                "health_facility_type": health_facility_type.id,
                "primary_health_care_center": primary_health_care_center.id,
            },
            "visibility_display": "RCRC Movement",
            "focal_person_loc": "Elliot Jele",
            "focal_person_en": "",
            "email": "",
            "phone": "",
        }
        self.authenticate()
        response = self.client.post("/api/v2/local-units/", data=data, format="json")
        self.assert_201(response)

        # Checking if the local unit is locked or not
        self.assertEqual(response.data["is_locked"], True)

        # validating the local unit
        local_unit_id = response.data["id"]
        self.client.force_authenticate(self.root_user)
        response = self.client.post(f"/api/v2/local-units/{local_unit_id}/validate/")
        self.assert_200(response)
        self.assertEqual(response.data["is_locked"], False)
        self.assertEqual(response.data["validated"], True)

        # saving the previous data
        previous_data = response.data

        # updating the local unit
        data["local_branch_name"] = "Updated local branch name"
        data["english_branch_name"] = "Updated english branch name"
        data["health"]["focal_point_email"] = "updatedemail@redcross.org.sz"
        response = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json")
        self.assert_200(response)
        self.assertEqual(response.data["local_branch_name"], data["local_branch_name"])

        # Reverting the local unit
        revert_data = {
            "reason": "Reverting the local unit test",
        }
        response = self.client.post(f"/api/v2/local-units/{local_unit_id}/revert/", data=revert_data, format="json")
        self.assert_200(response)

        # Checking if the local unit is reverted or not
        local_unit = LocalUnit.objects.get(id=local_unit_id)
        self.assertEqual(local_unit.local_branch_name, previous_data["local_branch_name"])
        self.assertEqual(local_unit.english_branch_name, previous_data["english_branch_name"])

        local_unit_change_request = LocalUnitChangeRequest.objects.filter(local_unit=local_unit).last()
        self.assertEqual(local_unit_change_request.status, LocalUnitChangeRequest.Status.REVERT)
        self.assertEqual(local_unit_change_request.rejected_reason, revert_data["reason"])
        # Checking if the local unit is unlocked
        self.assertEqual(local_unit.is_locked, False)
        self.assertEqual(local_unit.validated, True)

    def test_latest_changes(self):
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
            "type": type.id,
            "country": country.id,
            "created_at": "2024-05-13T06:53:14.978083Z",
            "modified_at": "2024-05-13T06:53:14.978099Z",
            "validated": True,
            "date_of_data": "2024-05-13",
            "level": level.id,
            "address_loc": "Silele Clinic is is in Hosea Inkhundla under the Shiselweni, Sigombeni is in Nkom'iyahlaba Inkhundla under the Manzini region and Mahwalala is in the Mbabane West Inkhundla under the Hhohho region.",  # noqa: E501
            "location_json": {
                "lat": 42.066667,
                "lng": 19.983333,
            },
            "health": {
                "focal_point_email": "jele@redcross.org.sz",
                "focal_point_phone_number": "26876088546",
                "affiliation": affiliation.id,
                "functionality": functionality.id,
                "health_facility_type": health_facility_type.id,
                "primary_health_care_center": primary_health_care_center.id,
            },
        }
        self.authenticate()
        response = self.client.post("/api/v2/local-units/", data=data, format="json")
        self.assert_201(response)

        # validating the local unit
        local_unit_id = response.data["id"]
        self.client.force_authenticate(self.root_user)
        response = self.client.post(f"/api/v2/local-units/{local_unit_id}/validate/")
        self.assert_200(response)

        # saving the previous data
        previous_data = response.data

        # Changing the local unit
        data["local_branch_name"] = "Updated local branch name"
        data["english_branch_name"] = "Updated english branch name"

        response = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json")
        self.assert_200(response)

        # Checking the latest changes
        response = self.client.get(f"/api/v2/local-units/{local_unit_id}/latest-change-request/")
        self.assert_200(response)
        self.assertEqual(response.data["previous_data_details"]["local_branch_name"], previous_data["local_branch_name"])
        self.assertEqual(response.data["previous_data_details"]["english_branch_name"], previous_data["english_branch_name"])

    def test_validate_local_unit(self):
        type = LocalUnitType.objects.create(code=0, name="Code 0")
        data = {
            "local_branch_name": "Silele Red Cross Clinic, Sigombeni Red Cross Clinic & Mahwalala Red Cross Clinic",
            "english_branch_name": None,
            "type": type.id,
            "country": self.country.id,
            "date_of_data": "2024-05-13",
            "location_json": {
                "lat": 42.066667,
                "lng": 19.983333,
            },
        }
        self.authenticate()
        response = self.client.post("/api/v2/local-units/", data=data, format="json")
        self.assert_201(response)

        local_unit_id = response.data["id"]
        # Testing For the local unit Global validator
        self.authenticate(self.global_validator_user)
        # validating the local unit by the Global validator
        response = self.client.post(f"/api/v2/local-units/{local_unit_id}/validate/")
        self.assert_200(response)
        local_unit_request = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit_id, status=LocalUnitChangeRequest.Status.APPROVED
        ).last()
        self.assertEqual(local_unit_request.current_validator, Validator.GLOBAL)

        # Testing For the local unit admin/Local validator
        self.authenticate(self.local_unit_admin_user)
        response = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json")
        self.assert_200(response)
        # validating the local unit by the local unit admin
        response = self.client.post(f"/api/v2/local-units/{local_unit_id}/validate/")
        local_unit_request = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit_id, status=LocalUnitChangeRequest.Status.APPROVED
        ).last()
        self.assertEqual(local_unit_request.current_validator, Validator.LOCAL)

        # Testing For the regional validator
        self.authenticate(self.regional_validator_user)
        response = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json")
        self.assert_200(response)
        # validating the local unit by the regional validator
        response = self.client.post(f"/api/v2/local-units/{local_unit_id}/validate/")
        local_unit_request = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit_id, status=LocalUnitChangeRequest.Status.APPROVED
        ).last()
        self.assertEqual(local_unit_request.current_validator, Validator.REGIONAL)

        # Testing for Root User/Global validator
        self.authenticate(self.root_user)
        response = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json")
        self.assert_200(response)
        # validating the local unit by the global validator
        response = self.client.post(f"/api/v2/local-units/{local_unit_id}/validate/")
        local_unit_request = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit_id, status=LocalUnitChangeRequest.Status.APPROVED
        ).last()
        self.assertEqual(local_unit_request.current_validator, Validator.GLOBAL)


class TestExternallyManagedLocalUnit(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.root_user = UserFactory.create(is_superuser=True)
        self.region = Region.objects.create(name=2)
        self.country1 = CountryFactory.create(
            name="Nepal",
            iso3="NLP",
            iso="NP",
            region=self.region,
            is_deprecated=False,
            independent=True,
            record_type=CountryType.COUNTRY,
        )
        self.country2 = CountryFactory.create(
            name="India",
            iso3="IND",
            region=self.region,
            is_deprecated=False,
            independent=True,
            record_type=CountryType.COUNTRY,
        )
        self.local_unit_type = LocalUnitType.objects.create(code=1, name="Code 0")

        self.externally_managed_local_unit = ExternallyManagedLocalUnitFactory.create(
            country=self.country1,
            local_unit_type=self.local_unit_type,
            created_by=self.user,
            updated_by=self.user,
        )

    def test_filter_by_country_name(self):
        self.client.force_authenticate(user=self.root_user)
        url = "/api/v2/externally-managed-local-unit/?country__name=Nepal"
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_country_iso3(self):
        self.client.force_authenticate(user=self.root_user)
        url = "/api/v2/externally-managed-local-unit/?country__iso3=IND"
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data["count"], 0)

    def test_filter_by_country_iso_invalid(self):
        self.client.force_authenticate(user=self.root_user)
        url = "/api/v2/externally-managed-local-unit/?country__iso=PH"
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data["count"], 0)

    def test_create_externally_managed_local_unit(self):
        url = "/api/v2/externally-managed-local-unit/"
        data = {"country": self.country2.id, "local_unit_type": self.local_unit_type.id, "enabled": True}
        # Without authentication
        response = self.client.patch(url, data=data, format="json")
        self.assert_401(response)

        # Normal user
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=data)
        self.assert_403(response)

        # Superuser
        self.client.force_authenticate(user=self.root_user)
        response = self.client.post(url, data=data)
        self.assert_201(response)

        # Try to create the duplicate
        self.client.force_authenticate(user=self.root_user)
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_update_externally_managed_local_unit(self):
        url = f"/api/v2/externally-managed-local-unit/{self.externally_managed_local_unit.id}/"
        data = {
            "enabled": True,
        }
        # Without authentication
        response = self.client.patch(url, data=data, format="json")
        self.assert_401(response)

        # Normal user
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(url, data=data, format="json")
        self.assert_403(response)

        # Superuser
        self.client.force_authenticate(user=self.root_user)
        response = self.client.patch(url, data=data, format="json")
        self.assert_200(response)

        self.externally_managed_local_unit.refresh_from_db()
        self.assertTrue(self.externally_managed_local_unit.enabled)

    def test_get_externally_managed_local_unit(self):
        url = "/api/v2/externally-managed-local-unit/"
        # Without authentication
        response = self.client.get(url)
        self.assert_401(response)

        # Normal user
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assert_403(response)

        # Superuser
        self.client.force_authenticate(user=self.root_user)
        response = self.client.get(url)
        self.assert_200(response)
