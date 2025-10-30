import datetime
import os
from unittest import mock

import factory
from django.contrib.auth.models import Group, Permission
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core import management
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from factory import fuzzy

from api.factories.country import CountryFactory
from api.factories.region import RegionFactory
from api.models import Country, CountryGeoms, CountryType, Region
from deployments.factories.user import UserFactory
from local_units.bulk_upload import BaseBulkUploadLocalUnit, BulkUploadHealthData
from main import settings
from main.test_case import APITestCase

from .models import (
    Affiliation,
    BloodService,
    DelegationOffice,
    DelegationOfficeType,
    ExternallyManagedLocalUnit,
    FacilityType,
    Functionality,
    GeneralMedicalService,
    HealthData,
    HospitalType,
    LocalUnit,
    LocalUnitBulkUpload,
    LocalUnitChangeRequest,
    LocalUnitLevel,
    LocalUnitType,
    PrimaryHCC,
    ProfessionalTrainingFacility,
    SpecializedMedicalService,
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


class LocalUnitTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LocalUnitType


class LocalUnitBulkUploadFactory(factory.django.DjangoModelFactory):
    country = factory.SubFactory(CountryFactory)
    local_unit_type = factory.SubFactory(LocalUnitTypeFactory)
    triggered_by = factory.SubFactory(UserFactory)
    status = LocalUnitBulkUpload.Status.PENDING

    class Meta:
        model = LocalUnitBulkUpload


class TestLocalUnitsListView(APITestCase):
    def setUp(self):
        super().setUp()
        region = Region.objects.create(name=2)
        country = CountryFactory.create(name="Nepal", iso3="NLP", iso="NP", region=region)
        country_1 = CountryFactory.create(
            name="Philippines",
            iso3="PHL",
            iso="PH",
            region=region,
        )
        type = LocalUnitType.objects.create(code=0, name="Code 0")
        type_1 = LocalUnitType.objects.create(code=1, name="Code 1")
        LocalUnitFactory.create_batch(
            5, country=country, type=type, draft=True, status=LocalUnit.Status.UNVALIDATED, date_of_data="2023-09-09"
        )
        LocalUnitFactory.create_batch(
            5, country=country_1, type=type_1, draft=False, status=LocalUnit.Status.VALIDATED, date_of_data="2023-08-08"
        )

        # test with Permission
        self.country2 = CountryFactory.create(
            name="India",
            iso3="IND",
            record_type=CountryType.COUNTRY,
            is_deprecated=False,
            independent=True,
            region=region,
        )
        self.type_3 = LocalUnitType.objects.create(code=3, name="Code 3")
        self.local_unit = LocalUnitFactory.create(
            country=self.country2, type=self.type_3, status=LocalUnit.Status.UNVALIDATED, date_of_data="2025-09-09"
        )
        self.local_unit_2 = LocalUnitFactory.create(
            country=self.country2, type=self.type_3, status=LocalUnit.Status.UNVALIDATED, date_of_data="2025-09-09"
        )
        management.call_command("make_local_unit_validator_permissions")
        self.normal_user = UserFactory.create()
        self.country_validator_user = UserFactory.create()
        self.region_validator_user = UserFactory.create()
        self.global_validator_user = UserFactory.create()
        #  permissions
        country_codename = f"local_unit_country_validator_{self.type_3.id}_{self.country2.id}"
        region_codename = f"local_unit_region_validator_{self.type_3.id}_{region.id}"
        global_codename = f"local_unit_global_validator_{self.type_3.id}"

        country_permission = Permission.objects.get(codename=country_codename)
        region_permission = Permission.objects.get(codename=region_codename)
        global_permission = Permission.objects.get(codename=global_codename)

        #  Country validator group
        country_group_name = f"Local unit validator for {self.type_3.name} {self.country2.name}"
        country_group = Group.objects.get(name=country_group_name)
        country_group.permissions.add(country_permission)
        self.country_validator_user.groups.add(country_group)

        # Region validator group
        region_group_name = f"Local unit validator for {self.type_3.name} {region.get_name_display()}"
        region_group = Group.objects.get(name=region_group_name)
        region_group.permissions.add(region_permission)
        self.region_validator_user.groups.add(region_group)

        # Global validator group
        global_group_name = f"Local unit global validator for {self.type_3.name}"

        global_group = Group.objects.get(name=global_group_name)
        global_group.permissions.add(global_permission)
        self.global_validator_user.groups.add(global_group)

    def test_list(self):
        self.authenticate()
        response = self.client.get("/api/v2/local-units/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 12)
        # TODO: fix these asaywltdi
        # self.assertEqual(response.data['results'][0]['location_details']['coordinates'], [12, 38])
        # self.assertEqual(response.data['results'][0]['country_details']['name'], 'Nepal')
        # self.assertEqual(response.data['results'][0]['country_details']['iso3'], 'NLP')
        # self.assertEqual(response.data['results'][0]['type_details']['name'], 'Code 0')
        # self.assertEqual(response.data['results'][0]['type_details']['code'], 0)

    def test_deprecate_local_unit(self):

        # test with country validator Permission
        self.client.force_authenticate(self.country_validator_user)
        url = f"/api/v2/local-units/{self.local_unit.id}/deprecate/"
        data = {
            "deprecated_reason": LocalUnit.DeprecateReason.INCORRECTLY_ADDED,
            "deprecated_reason_overview": "test reason",
        }
        response = self.client.post(url, data=data)
        local_unit_obj = LocalUnit.objects.get(id=self.local_unit.id)

        self.assert_200(response)
        self.assertEqual(local_unit_obj.is_deprecated, True)
        self.assertEqual(local_unit_obj.deprecated_reason, LocalUnit.DeprecateReason.INCORRECTLY_ADDED)

        # Test for validation
        response = self.client.post(url, data=data)
        self.assert_404(response)

        # Test revert deprecate
        self.client.force_authenticate(self.country_validator_user)
        url = f"/api/v2/local-units/{self.local_unit.id}/revert-deprecate/"
        response = self.client.post(url)
        local_unit_obj = LocalUnit.objects.get(id=self.local_unit.id)
        self.assert_200(response)
        self.assertEqual(local_unit_obj.is_deprecated, False)
        self.assertEqual(local_unit_obj.deprecated_reason, None)
        self.assertEqual(local_unit_obj.deprecated_reason_overview, "")

        # Test with super user
        self.client.force_authenticate(self.root_user)
        url = f"/api/v2/local-units/{self.local_unit_2.id}/deprecate/"
        response = self.client.post(url, data=data)
        local_unit_obj = LocalUnit.objects.get(id=self.local_unit_2.id)
        self.assert_200(response)
        self.assertEqual(local_unit_obj.is_deprecated, True)
        self.assertEqual(local_unit_obj.deprecated_reason, LocalUnit.DeprecateReason.INCORRECTLY_ADDED)

        # Test revert deprecate
        self.client.force_authenticate(self.root_user)
        url = f"/api/v2/local-units/{self.local_unit_2.id}/revert-deprecate/"
        response = self.client.post(url)
        local_unit_obj = LocalUnit.objects.get(id=self.local_unit_2.id)
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
        self.assertEqual(response.data["count"], 7)

        response = self.client.get("/api/v2/local-units/?status=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 5)

        response = self.client.get("/api/v2/local-units/?status=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 7)


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
        self.normal_user = UserFactory.create()

        self.region = RegionFactory.create(name=2, label="Asia Pacific")
        self.country = CountryFactory.create(
            name="Nepal",
            iso3="NPL",
            record_type=CountryType.COUNTRY,
            is_deprecated=False,
            independent=True,
            region=self.region,
        )

        self.local_unit_type = LocalUnitType.objects.create(code=1, name="administrative")
        management.call_command("make_permissions")
        management.call_command("make_local_unit_validator_permissions")
        self.country_admin_user = UserFactory.create()
        self.country_validator_user = UserFactory.create()
        self.region_validator_user = UserFactory.create()
        self.global_validator_user = UserFactory.create()
        #  permissions
        country_admin_codename = f"country_admin_{self.country.id}"
        country_codename = f"local_unit_country_validator_{self.local_unit_type.id}_{self.country.id}"
        region_codename = f"local_unit_region_validator_{self.local_unit_type.id}_{self.region.id}"
        global_codename = f"local_unit_global_validator_{self.local_unit_type.id}"

        country_admin_permission = Permission.objects.get(codename=country_admin_codename)
        country_permission = Permission.objects.get(codename=country_codename)
        region_permission = Permission.objects.get(codename=region_codename)
        global_permission = Permission.objects.get(codename=global_codename)

        # Country admin group
        country__admin_group_name = "%s Admins" % self.country.name
        country__admin_group = Group.objects.get(name=country__admin_group_name)
        country__admin_group.permissions.add(country_admin_permission)
        self.country_admin_user.groups.add(country__admin_group)
        #  Country validator group
        country_group_name = f"Local unit validator for {self.local_unit_type.name} {self.country.name}"
        country_group = Group.objects.get(name=country_group_name)
        country_group.permissions.add(country_permission)
        self.country_validator_user.groups.add(country_group)

        # Region validator group
        region_group_name = f"Local unit validator for {self.local_unit_type.name} {self.region.get_name_display()}"
        region_group = Group.objects.get(name=region_group_name)
        region_group.permissions.add(region_permission)
        self.region_validator_user.groups.add(region_group)

        # Global validator group
        global_group_name = f"Local unit global validator for {self.local_unit_type.name}"

        global_group = Group.objects.get(name=global_group_name)
        global_group.permissions.add(global_permission)
        self.global_validator_user.groups.add(global_group)

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
        self.assertEqual(response.data["status"], LocalUnit.Status.UNVALIDATED)

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
            "update_reason_overview": "Needed update for testing",
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
                "other_profiles": [
                    {"number": 2, "position": "Nurse"},
                    {"number": 3, "position": "Doctor"},
                ],
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
        self.assertEqual(response.data["status"], LocalUnit.Status.UNVALIDATED)
        #  Local unit should not be updated, until it is validated
        local_unit_id = response.data["id"]
        response = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json")
        self.assert_400(response)

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
            "update_reason_overview": "Needed update for testing",
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
        # Checking if the local unit status is unvalidated or not
        self.assertEqual(response.data["status"], LocalUnit.Status.UNVALIDATED)
        # validating the local unit
        local_unit_id = response.data["id"]
        self.client.force_authenticate(self.root_user)
        response = self.client.post(f"/api/v2/local-units/{local_unit_id}/validate/")
        self.assert_200(response)
        self.assertEqual(response.data["status"], LocalUnit.Status.VALIDATED)
        # saving the previous data
        previous_data = response.data

        # updating the local unit
        data["local_branch_name"] = "Updated local branch name"
        data["english_branch_name"] = "Updated english branch name"
        data["health"]["focal_point_email"] = "updatedemail@redcross.org.sz"
        response = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json")
        self.assert_200(response)
        self.assertEqual(response.data["local_branch_name"], data["local_branch_name"])
        self.assertEqual(response.data["status"], LocalUnit.Status.PENDING_EDIT_VALIDATION)
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
        # Checking if the local unit is validated or not
        self.assertEqual(local_unit.status, LocalUnit.Status.VALIDATED)

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
            "date_of_data": "2024-05-13",
            "level": level.id,
            "address_loc": "Silele Clinic is is in Hosea Inkhundla under the Shiselweni, Sigombeni is in Nkom'iyahlaba Inkhundla under the Manzini region and Mahwalala is in the Mbabane West Inkhundla under the Hhohho region.",  # noqa: E501
            "update_reason_overview": "Needed update for testing",
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
        self.assertEqual(response.data["status"], LocalUnit.Status.VALIDATED)
        # saving the previous data
        previous_data = response.data

        # Changing the local unit
        data["local_branch_name"] = "Updated local branch name"
        data["english_branch_name"] = "Updated english branch name"

        response = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json")
        self.assert_200(response)
        self.assertEqual(response.data["status"], LocalUnit.Status.PENDING_EDIT_VALIDATION)
        # Checking the latest changes
        response = self.client.get(f"/api/v2/local-units/{local_unit_id}/latest-change-request/")
        self.assert_200(response)
        self.assertEqual(response.data["previous_data_details"]["local_branch_name"], previous_data["local_branch_name"])
        self.assertEqual(response.data["previous_data_details"]["english_branch_name"], previous_data["english_branch_name"])

    def test_validate_local_unit(self):
        data = {
            "local_branch_name": "Silele Red Cross Clinic, Sigombeni Red Cross Clinic & Mahwalala Red Cross Clinic",
            "english_branch_name": None,
            "type": self.local_unit_type.id,
            "country": self.country.id,
            "date_of_data": "2024-05-13",
            "location_json": {
                "lat": 42.066667,
                "lng": 19.983333,
            },
            "update_reason_overview": "Needed update for testing",
        }
        self.authenticate()
        response = self.client.post("/api/v2/local-units/", data=data, format="json")
        self.assert_201(response)
        self.assertEqual(response.data["status"], LocalUnit.Status.UNVALIDATED)
        local_unit_id = response.data["id"]
        self.authenticate(self.global_validator_user)
        # validating the local unit by the Global validator
        response = self.client.post(f"/api/v2/local-units/{local_unit_id}/validate/")
        self.assert_200(response)
        local_unit_request = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit_id, status=LocalUnitChangeRequest.Status.APPROVED
        ).last()
        self.assertEqual(local_unit_request.current_validator, Validator.GLOBAL)
        self.assertEqual(response.data["status"], LocalUnit.Status.VALIDATED)

        # Testing For the local unit admin/country validator
        self.authenticate(self.country_validator_user)
        response = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json")
        self.assert_200(response)
        # validating the local unit by the local unit region admin
        self.authenticate(self.country_validator_user)
        response = self.client.post(f"/api/v2/local-units/{local_unit_id}/validate/")
        local_unit_request = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit_id, status=LocalUnitChangeRequest.Status.APPROVED
        ).last()
        self.assertEqual(local_unit_request.current_validator, Validator.LOCAL)
        self.assertEqual(response.data["status"], LocalUnit.Status.VALIDATED)

        # Testing For the regional validator
        self.authenticate(self.region_validator_user)
        response = self.client.put(f"/api/v2/local-units/{local_unit_id}/", data=data, format="json")
        self.assert_200(response)
        # validating the local unit by the regional validator
        response = self.client.post(f"/api/v2/local-units/{local_unit_id}/validate/")
        local_unit_request = LocalUnitChangeRequest.objects.filter(
            local_unit=local_unit_id, status=LocalUnitChangeRequest.Status.APPROVED
        ).last()
        self.assertEqual(local_unit_request.current_validator, Validator.REGIONAL)
        self.assertEqual(response.data["status"], LocalUnit.Status.VALIDATED)

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
        self.assertEqual(response.data["status"], LocalUnit.Status.VALIDATED)

    def test_create_local_unit_with_externally_managed_country_and_type(self):
        # Externally managed
        country = CountryFactory.create(
            name="India",
            iso3="IND",
            record_type=CountryType.COUNTRY,
            is_deprecated=False,
            independent=True,
            region=self.region,
        )

        local_unit_type = LocalUnitType.objects.create(code=6, name="other")
        level = LocalUnitLevel.objects.create(level=1, name="Code 1")
        ExternallyManagedLocalUnitFactory.create(country=country, local_unit_type=local_unit_type, enabled=True)

        data = {
            "local_branch_name": "Test branch name",
            "english_brancself.h_name": "Test branch name",
            "type": local_unit_type.id,
            "country": country.id,
            "draft": False,
            "postcode": "4407",
            "address_loc": "4407",
            "address_en": "",
            "city_loc": "",
            "city_en": "Pukë",
            "link": "",
            "location_json": {
                "lat": 20.5937,
                "lng": 78.9629,
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
        }
        # without authentication
        response = self.client.post("/api/v2/local-units/", data=data, format="json")
        self.assertEqual(response.status_code, 401)
        # with super user
        self.client.force_authenticate(user=self.root_user)
        response = self.client.post("/api/v2/local-units/", data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(LocalUnitChangeRequest.objects.count(), 0)

    def test_country_region_admin_permission_for_local_unit_update(self):
        region1 = RegionFactory.create(name=2, label="Asia Pacific")

        region2 = RegionFactory.create(name=0, label="Africa")

        country = CountryFactory.create(
            name="India",
            iso3="IND",
            record_type=CountryType.COUNTRY,
            is_deprecated=False,
            independent=True,
            region=region1,
        )
        self.asia_admin = UserFactory.create(email="asia@admin.com")
        self.africa_admin = UserFactory.create(email="africa@admin.com")
        self.india_admin = UserFactory.create(email="india@admin.com")
        # India admin setup
        management.call_command("make_permissions")
        country_admin_codename = f"country_admin_{country.id}"
        country_admin_permission = Permission.objects.get(codename=country_admin_codename)
        country_admin_group_name = "%s Admins" % country.name
        country_admin_group = Group.objects.get(name=country_admin_group_name)
        country_admin_group.permissions.add(country_admin_permission)
        self.india_admin.groups.add(country_admin_group)
        # Asia admin
        asia_admin_codename = f"region_admin_{region1.id}"
        asia_admin_permission = Permission.objects.get(codename=asia_admin_codename)
        asia_admin_group_name = "%s Regional Admins" % region1.name
        asia_admin_group = Group.objects.get(name=asia_admin_group_name)
        asia_admin_group.permissions.add(asia_admin_permission)
        self.asia_admin.groups.add(asia_admin_group)

        # Africa admin
        africa_admin_codename = f"region_admin_{region2.id}"
        africa_admin_permission = Permission.objects.get(codename=africa_admin_codename)
        africa_admin_group_name = "%s Regional Admins" % region2.name
        africa_admin_group = Group.objects.get(name=africa_admin_group_name)
        africa_admin_group.permissions.add(africa_admin_permission)
        self.africa_admin.groups.add(africa_admin_group)

        local_unit = LocalUnitFactory.create(
            country=country,
            type=self.local_unit_type,
            draft=False,
            status=LocalUnit.Status.VALIDATED,
            date_of_data="2023-08-08",
        )
        local_unit2 = LocalUnitFactory.create(
            country=country,
            type=self.local_unit_type,
            draft=False,
            status=LocalUnit.Status.VALIDATED,
            date_of_data="2023-08-08",
        )
        url = f"/api/v2/local-units/{local_unit.id}/"
        data = {
            "local_branch_name": "Updated local branch name",
            "update_reason_overview": "Needed update for testing",
            "type": self.local_unit_type.id,
            "location_json": {
                "lat": 20.5937,
                "lng": 78.9629,
            },
        }
        response = self.client.patch(url, data=data, format="json")
        self.assert_401(response)
        # Test: different country admin
        self.authenticate(self.country_admin_user)
        response = self.client.patch(url, data=data, format="json")
        self.assert_403(response)
        # Test: actual country admin
        self.authenticate(self.india_admin)
        response = self.client.patch(url, data=data, format="json")
        self.assert_200(response)
        self.assertEqual(response.data["local_branch_name"], "Updated local branch name")

        url = f"/api/v2/local-units/{local_unit2.id}/"
        # Test: different region admin
        self.authenticate(self.africa_admin)
        response = self.client.patch(url, data=data, format="json")
        self.assert_403(response)
        # Test: same region admin
        self.authenticate(self.asia_admin)
        response = self.client.patch(url, data=data, format="json")
        self.assert_200(response)
        self.assertEqual(response.data["local_branch_name"], "Updated local branch name")


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
        self.client.force_authenticate(user=self.user)
        url = "/api/v2/externally-managed-local-unit/?country__name=Nepal"
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_country_iso3(self):
        self.client.force_authenticate(user=self.user)
        url = "/api/v2/externally-managed-local-unit/?country__iso3=IND"
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data["count"], 0)

    def test_filter_by_country_iso_invalid(self):
        self.client.force_authenticate(user=self.user)
        url = "/api/v2/externally-managed-local-unit/?country__iso=PH"
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data["count"], 0)

    def test_filter_by_country_id(self):
        self.client.force_authenticate(user=self.user)
        url = f"/api/v2/externally-managed-local-unit/?country__id={self.country1.id}"
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(response.data["count"], 1)

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
        self.assert_200(response)

        # Superuser
        self.client.force_authenticate(user=self.root_user)
        response = self.client.get(url)
        self.assert_200(response)


class LocalUnitBulkUploadTests(APITestCase):

    def setUp(self):
        super().setUp()
        self.normal_user = UserFactory.create()
        self.region = RegionFactory.create(name=2, label="Asia Pacific")
        self.region2 = RegionFactory.create(name=0, label="Africa")

        #  countries
        self.country1 = CountryFactory.create(
            name="Nepal", iso3="NPL", record_type=CountryType.COUNTRY, is_deprecated=False, independent=True, region=self.region
        )
        self.country2 = CountryFactory.create(
            name="India", iso3="IND", record_type=CountryType.COUNTRY, is_deprecated=False, independent=True, region=self.region
        )
        self.country3 = CountryFactory.create(
            name="Bangladesh",
            iso3="BGD",
            record_type=CountryType.COUNTRY,
            is_deprecated=False,
            independent=True,
            region=self.region,
        )
        self.country4 = CountryFactory.create(
            name="Nigeria",
            iso3="NGA",
            record_type=CountryType.COUNTRY,
            is_deprecated=False,
            independent=True,
            region=self.region2,
        )

        # local unit types
        self.lut1 = LocalUnitType.objects.create(code=1, name="Code 1")
        self.lut2 = LocalUnitType.objects.create(code=2, name="Code 2")
        self.lut3 = LocalUnitType.objects.create(code=3, name="Code 3")

        # Create corresponding externally managed local units
        ExternallyManagedLocalUnitFactory.create(country=self.country1, local_unit_type=self.lut1, enabled=True)
        ExternallyManagedLocalUnitFactory.create(country=self.country2, local_unit_type=self.lut2, enabled=True)
        ExternallyManagedLocalUnitFactory.create(country=self.country4, local_unit_type=self.lut2, enabled=True)

        # Run permission creation logic
        management.call_command("make_local_unit_validator_permissions")

        # Create 3 validator users
        self.country_validator_user = UserFactory.create()
        self.country_validator_user2 = UserFactory.create()
        self.region_validator_user = UserFactory.create()
        self.global_validator_user = UserFactory.create()

        # Set up permissions and groups

        # --- Country validator ---
        country_codename = f"local_unit_country_validator_{self.lut1.id}_{self.country1.id}"
        country_permission = Permission.objects.get(codename=country_codename)
        country_group_name = f"Local unit validator for {self.lut1.name} {self.country1.name}"
        country_group = Group.objects.get(name=country_group_name)
        country_group.permissions.add(country_permission)
        self.country_validator_user.groups.add(country_group)

        # --- Country validator 2 ---

        country_codename = f"local_unit_country_validator_{self.lut1.id}_{self.country2.id}"
        country_permission = Permission.objects.get(codename=country_codename)
        country_group_name = f"Local unit validator for {self.lut1.name} {self.country2.name}"
        country_group = Group.objects.get(name=country_group_name)
        country_group.permissions.add(country_permission)
        self.country_validator_user2.groups.add(country_group)

        # --- Region validator ---
        region_codename = f"local_unit_region_validator_{self.lut1.id}_{self.region.id}"
        region_permission = Permission.objects.get(codename=region_codename)
        region_group_name = f"Local unit validator for {self.lut1.name} {self.region.get_name_display()}"
        region_group = Group.objects.get(name=region_group_name)
        region_group.permissions.add(region_permission)
        self.region_validator_user.groups.add(region_group)

        # --- Global validator ---
        global_codename = f"local_unit_global_validator_{self.lut1.id}"
        global_permission = Permission.objects.get(codename=global_codename)
        global_group_name = f"Local unit global validator for {self.lut1.name}"
        global_group = Group.objects.get(name=global_group_name)
        global_group.permissions.add(global_permission)
        self.global_validator_user.groups.add(global_group)

        file_path = os.path.join(settings.TEST_DIR, "local_unit/test.csv")
        with open(file_path, "rb") as f:
            self._file_content = f.read()

    def create_upload_file(self, filename="test.csv"):
        """
        Always return a new file instance to prevent stream exhaustion.
        """
        return SimpleUploadedFile(filename, self._file_content, content_type="text/csv")

    @mock.patch("local_units.tasks.process_bulk_upload_local_unit.delay")
    def test_bulk_upload_local_unit(self, mock_delay):
        url = "/api/v2/bulk-upload-local-unit/"

        # Unauthenticated request
        data = {
            "country": self.country1.id,
            "local_unit_type": self.lut1.id,
            "file": self.create_upload_file(),
        }
        response = self.client.post(url, data=data, format="multipart")
        self.assert_401(response)

        # Superuser - with externally managed data
        self.client.force_authenticate(user=self.root_user)
        data = {
            "country": self.country1.id,
            "local_unit_type": self.lut1.id,
            "file": self.create_upload_file(),
        }
        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post(url, data=data, format="multipart")
        self.assert_201(response)
        mock_delay.assert_called()

        # Superuser - Without externally managed data
        self.client.force_authenticate(user=self.root_user)
        data = {
            "country": self.country3.id,
            "local_unit_type": self.lut3.id,
            "file": self.create_upload_file(),
        }
        response = self.client.post(url, data=data, format="multipart")
        self.assert_400(response)

        # Country validator - matching country
        self.client.force_authenticate(user=self.country_validator_user)
        data = {
            "country": self.country1.id,
            "local_unit_type": self.lut1.id,
            "file": self.create_upload_file(),
        }
        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post(url, data=data, format="multipart")
        self.assert_201(response)
        mock_delay.assert_called()

        # Country validator - different country
        self.client.force_authenticate(user=self.country_validator_user2)
        data = {
            "country": self.country4.id,
            "local_unit_type": self.lut2.id,
            "file": self.create_upload_file(),
        }
        response = self.client.post(url, data=data, format="multipart")
        self.assert_403(response)

        # Region validator - same region
        self.client.force_authenticate(user=self.region_validator_user)
        data = {
            "country": self.country1.id,
            "local_unit_type": self.lut1.id,
            "file": self.create_upload_file(),
        }
        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post(url, data=data, format="multipart")
        self.assert_201(response)
        mock_delay.assert_called()

        # Region validator - different region
        self.client.force_authenticate(user=self.region_validator_user)
        data = {
            "country": self.country4.id,
            "local_unit_type": self.lut2.id,
            "file": self.create_upload_file(),
        }
        response = self.client.post(url, data=data, format="multipart")
        self.assert_403(response)
        # global validator
        self.client.force_authenticate(user=self.global_validator_user)
        data = {
            "country": self.country1.id,
            "local_unit_type": self.lut1.id,
            "file": self.create_upload_file(),
        }
        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post(url, data=data, format="multipart")
        self.assert_201(response)
        mock_delay.assert_called()


class BulkUploadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create(is_superuser=True)
        cls.region = RegionFactory.create(name=2, label="Asia Pacific")
        cls.region2 = RegionFactory.create(name=1, label="Americas")

        cls.country1 = CountryFactory.create(
            name="Afghanistan",
            iso3="AFG",
            record_type=CountryType.COUNTRY,
            is_deprecated=False,
            independent=True,
            region=cls.region,
            centroid=Point(65.0, 33.0),
            bbox=Polygon(
                (
                    (60.0, 29.0),
                    (75.0, 29.0),
                    (75.0, 38.0),
                    (60.0, 38.0),
                    (60.0, 29.0),
                )
            ),
        )

        cls.country2 = CountryFactory.create(
            name="Brazil",
            iso3="BRA",
            record_type=CountryType.COUNTRY,
            is_deprecated=False,
            independent=True,
            region=cls.region2,
            centroid=Point(-47.8825, -15.7942),
            bbox=Polygon(
                (
                    (-74.0, -34.0),
                    (-34.0, -34.0),
                    (-34.0, 5.0),
                    (-74.0, 5.0),
                    (-74.0, -34.0),
                )
            ),
        )

        cls.country1_geom = CountryGeoms.objects.create(country=cls.country1, geom=MultiPolygon(cls.country1.bbox))

        cls.country2_geom = CountryGeoms.objects.create(country=cls.country2, geom=MultiPolygon(cls.country2.bbox))

        cls.local_unit_type = LocalUnitType.objects.create(code=1, name="Administrative")
        cls.local_unit_type2 = LocalUnitType.objects.create(code=2, name="Health Care")
        cls.level = LocalUnitLevel.objects.create(level=0, name="National")
        file_path = os.path.join(settings.TEST_DIR, "local_unit/test.csv")
        with open(file_path, "rb") as f:
            cls._file_content = f.read()

    def create_upload_file(cls, filename="test.csv"):
        return SimpleUploadedFile(filename, cls._file_content, content_type="text/csv")

    def test_bulk_upload_with_incorrect_country(cls):
        """
        Test bulk upload fails when the country does not match CSV data.
        """
        cls.bulk_upload = LocalUnitBulkUploadFactory.create(
            country=cls.country1,
            local_unit_type=cls.local_unit_type,
            triggered_by=cls.user,
            file=cls.create_upload_file(),
            status=LocalUnitBulkUpload.Status.PENDING,
        )
        runner = BaseBulkUploadLocalUnit(cls.bulk_upload)
        runner.run()

        cls.bulk_upload.refresh_from_db()

        cls.assertEqual(cls.bulk_upload.status, LocalUnitBulkUpload.Status.FAILED)
        cls.assertEqual(runner.success_count, 0)
        cls.assertEqual(runner.failed_count, 3)
        # Check that error_file is saved
        error_file = cls.bulk_upload.error_file
        cls.assertIsNotNone(error_file)

    def test_bulk_upload_with_valid_country(cls):
        """
        Test bulk upload succeeds when the country matches CSV data
        """
        cls.bulk_upload = LocalUnitBulkUploadFactory.create(
            country=cls.country2,  # Brazil
            local_unit_type=cls.local_unit_type,
            triggered_by=cls.user,
            file=cls.create_upload_file(),  # CSV with Brazil rows
            status=LocalUnitBulkUpload.Status.PENDING,
        )
        runner = BaseBulkUploadLocalUnit(cls.bulk_upload)
        runner.run()

        cls.bulk_upload.refresh_from_db()
        cls.assertEqual(cls.bulk_upload.status, LocalUnitBulkUpload.Status.SUCCESS)
        cls.assertEqual(runner.success_count, 3)
        cls.assertEqual(runner.failed_count, 0)

    def test_bulk_upload_fails_and_delete(cls):
        """
        Test bulk upload fails and delete when CSV has incorrect data.
        """
        LocalUnitFactory.create_batch(
            5,
            country=cls.country1,
            type=cls.local_unit_type,
            created_by=cls.user,
            level=cls.level,
        )
        cls.bulk_upload = LocalUnitBulkUploadFactory.create(
            country=cls.country1,
            local_unit_type=cls.local_unit_type,
            triggered_by=cls.user,
            file=cls.create_upload_file(),
            status=LocalUnitBulkUpload.Status.PENDING,
        )
        runner = BaseBulkUploadLocalUnit(cls.bulk_upload)
        runner.run()
        cls.bulk_upload.refresh_from_db()
        cls.assertEqual(cls.bulk_upload.status, LocalUnitBulkUpload.Status.FAILED)
        cls.assertEqual(runner.failed_count, 3)
        # Assert that existing local unit is not deleted
        cls.assertEqual(LocalUnit.objects.count(), 5)
        # Check that error_file is saved
        error_file = cls.bulk_upload.error_file
        cls.assertIsNotNone(error_file)

    def test_bulk_upload_deletes_old_and_creates_new_local_units(cls):
        """
        Test bulk upload with correct CSV data.
        """
        old_local_unit = LocalUnitFactory.create(
            country=cls.country2,
            type=cls.local_unit_type,
            created_by=cls.user,
            level=cls.level,
        )
        cls.old_local_unit_id = old_local_unit.pk
        cls.bulk_upload = LocalUnitBulkUploadFactory.create(
            country=cls.country2,  # Brazil
            local_unit_type=cls.local_unit_type,
            triggered_by=cls.user,
            file=cls.create_upload_file(),
            status=LocalUnitBulkUpload.Status.PENDING,
        )
        runner = BaseBulkUploadLocalUnit(cls.bulk_upload)
        runner.run()
        cls.bulk_upload.refresh_from_db()
        cls.assertEqual(cls.bulk_upload.status, LocalUnitBulkUpload.Status.SUCCESS)
        cls.assertEqual(runner.success_count, 3)
        cls.assertEqual(runner.failed_count, 0)
        # Check old local unit is deleted
        cls.assertFalse(LocalUnit.objects.filter(pk=cls.old_local_unit_id).exists())
        # Check new local units count equals rows in CSV
        cls.assertEqual(LocalUnit.objects.count(), 3)

    def test_empty_administrative_file(cls):
        """
        Test bulk upload file is empty
        """

        file_path = os.path.join(settings.STATICFILES_DIRS[0], "files", "local_units", "local-unit-bulk-upload-template.csv")
        with open(file_path, "rb") as f:
            file_content = f.read()
        empty_file = SimpleUploadedFile(name="local-unit-bulk-upload-template.csv", content=file_content, content_type="text/csv")
        LocalUnitFactory.create_batch(
            5,
            country=cls.country2,
            type=cls.local_unit_type,
            created_by=cls.user,
            level=cls.level,
        )

        cls.bulk_upload = LocalUnitBulkUpload.objects.create(
            file=empty_file,
            country=cls.country2,
            local_unit_type=cls.local_unit_type,
            triggered_by=cls.user,
            status=LocalUnitBulkUpload.Status.PENDING,
        )
        runner = BaseBulkUploadLocalUnit(cls.bulk_upload)
        runner.run()

        cls.bulk_upload.refresh_from_db()
        cls.assertEqual(cls.bulk_upload.status, LocalUnitBulkUpload.Status.FAILED)
        cls.assertIsNotNone(cls.bulk_upload.error_message)
        cls.assertEqual(LocalUnit.objects.count(), 5)


class BulkUploadHealthDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create(is_superuser=True)
        cls.region = RegionFactory.create(name=2, label="Asia Pacific")
        cls.region2 = RegionFactory.create(name=1, label="Americas")

        cls.country1 = CountryFactory.create(
            name="Afghanistan",
            iso3="AFG",
            record_type=CountryType.COUNTRY,
            is_deprecated=False,
            independent=True,
            region=cls.region,
            centroid=Point(65.0, 33.0),
            bbox=Polygon(
                (
                    (60.0, 29.0),
                    (75.0, 29.0),
                    (75.0, 38.0),
                    (60.0, 38.0),
                    (60.0, 29.0),
                )
            ),
        )

        cls.country2 = CountryFactory.create(
            name="Brazil",
            iso3="BRA",
            record_type=CountryType.COUNTRY,
            is_deprecated=False,
            independent=True,
            region=cls.region2,
            centroid=Point(-47.8825, -15.7942),
            bbox=Polygon(
                (
                    (-74.0, -34.0),
                    (-34.0, -34.0),
                    (-34.0, 5.0),
                    (-74.0, 5.0),
                    (-74.0, -34.0),
                )
            ),
        )

        cls.country1_geom = CountryGeoms.objects.create(country=cls.country1, geom=MultiPolygon(cls.country1.bbox))
        cls.country2_geom = CountryGeoms.objects.create(country=cls.country2, geom=MultiPolygon(cls.country2.bbox))

        cls.local_unit_type = LocalUnitType.objects.create(code=2, name="Health Care")

        cls.level = LocalUnitLevel.objects.create(level=0, name="National")
        cls.affiliation = Affiliation.objects.create(code=2, name="Public Government Facility")
        cls.functionality = Functionality.objects.create(code=1, name="Fully Functional")
        cls.health_facility_type = FacilityType.objects.create(code=1, name="Ambulance Station")
        cls.hospital_type = HospitalType.objects.create(code=2, name=" Mental Health Hospital")
        # health data many-to-many field
        cls.specialized_medical_beyond_primary_level = SpecializedMedicalService.objects.create(code=1, name="Anaesthesiology")
        cls.blood_services = BloodService.objects.create(code=1, name="Blood Collection")
        cls.professional_training_facilities = ProfessionalTrainingFacility.objects.create(code=1, name="Nurses")
        cls.general_medical_services = GeneralMedicalService.objects.create(code=1, name="Minor Trauma")

        file_path = os.path.join(settings.TEST_DIR, "local_unit/test-health.csv")
        with open(file_path, "rb") as f:
            cls._file_content = f.read()

    def create_upload_file(cls, filename="test-health.csv"):
        return SimpleUploadedFile(filename, cls._file_content, content_type="text/csv")

    def test_bulk_upload_health_with_incorrect_country(cls):
        """
        Should fail when CSV rows are not equal to bulk upload country.
        """
        cls.bulk_upload = LocalUnitBulkUploadFactory.create(
            country=cls.country1,
            local_unit_type=cls.local_unit_type,
            triggered_by=cls.user,
            file=cls.create_upload_file(),
            status=LocalUnitBulkUpload.Status.PENDING,
        )

        runner = BulkUploadHealthData(cls.bulk_upload)
        runner.run()

        cls.bulk_upload.refresh_from_db()
        cls.assertEqual(cls.bulk_upload.status, LocalUnitBulkUpload.Status.FAILED)
        cls.assertEqual(runner.success_count, 0)
        cls.assertEqual(runner.failed_count, 3)
        cls.assertIsNotNone(cls.bulk_upload.error_file)

    def test_bulk_upload_health_fails_and_does_not_delete(cls):
        """
        Should fail and keep existing LocalUnits & HealthData when CSV invalid.
        """
        health_data = HealthDataFactory.create_batch(
            5,
            functionality=cls.functionality,
            affiliation=cls.affiliation,
            health_facility_type=cls.health_facility_type,
            hospital_type=cls.hospital_type,
        )
        LocalUnitFactory.create_batch(
            5,
            country=cls.country1,
            type=cls.local_unit_type,
            created_by=cls.user,
            level=cls.level,
            health=factory.Iterator(health_data),
        )

        cls.bulk_upload = LocalUnitBulkUploadFactory.create(
            country=cls.country1,
            local_unit_type=cls.local_unit_type,
            triggered_by=cls.user,
            file=cls.create_upload_file(),  # Brazil rows
            status=LocalUnitBulkUpload.Status.PENDING,
        )

        runner = BulkUploadHealthData(cls.bulk_upload)
        runner.run()

        cls.bulk_upload.refresh_from_db()
        cls.assertEqual(cls.bulk_upload.status, LocalUnitBulkUpload.Status.FAILED)
        cls.assertEqual(runner.failed_count, 3)
        cls.assertEqual(LocalUnit.objects.count(), 5)
        cls.assertEqual(HealthData.objects.count(), 5)
        cls.assertIsNotNone(cls.bulk_upload.error_file)

    def test_bulk_upload_health_deletes_old_and_creates_new(cls):
        """
        Should delete old LocalUnits & HealthData and create new from CSV.
        """
        old_health = HealthDataFactory.create(
            functionality=cls.functionality,
            affiliation=cls.affiliation,
            health_facility_type=cls.health_facility_type,
            hospital_type=cls.hospital_type,
        )
        old_local_unit = LocalUnitFactory.create(
            country=cls.country2,
            type=cls.local_unit_type,
            created_by=cls.user,
            level=cls.level,
            health=old_health,
        )
        cls.bulk_upload = LocalUnitBulkUploadFactory.create(
            country=cls.country2,
            local_unit_type=cls.local_unit_type,
            triggered_by=cls.user,
            file=cls.create_upload_file(),
            status=LocalUnitBulkUpload.Status.PENDING,
        )
        runner = BulkUploadHealthData(cls.bulk_upload)
        runner.run()
        cls.bulk_upload.refresh_from_db()
        cls.assertEqual(cls.bulk_upload.status, LocalUnitBulkUpload.Status.SUCCESS)
        cls.assertEqual(runner.success_count, 3)
        cls.assertEqual(runner.failed_count, 0)
        # Old data deleted
        cls.assertFalse(LocalUnit.objects.filter(pk=old_local_unit.id).exists())
        cls.assertFalse(HealthData.objects.filter(pk=old_health.id).exists())
        # New local units & health data count matches CSV
        cls.assertEqual(LocalUnit.objects.count(), 3)
        cls.assertEqual(HealthData.objects.count(), 3)

    def test_empty_health_template_file(cls):
        """
        Test upload file is empty
        """

        file_path = os.path.join(
            settings.STATICFILES_DIRS[0], "files", "local_units", "local-unit-health-bulk-upload-template.csv"
        )
        with open(file_path, "rb") as f:
            file_content = f.read()
        empty_file = SimpleUploadedFile(
            name="local-unit-health-bulk-upload-template.csv", content=file_content, content_type="text/csv"
        )
        health_data = HealthDataFactory.create_batch(
            5,
            functionality=cls.functionality,
            affiliation=cls.affiliation,
            health_facility_type=cls.health_facility_type,
            hospital_type=cls.hospital_type,
        )
        LocalUnitFactory.create_batch(
            5,
            country=cls.country1,
            type=cls.local_unit_type,
            created_by=cls.user,
            level=cls.level,
            health=factory.Iterator(health_data),
        )

        cls.bulk_upload = LocalUnitBulkUpload.objects.create(
            file=empty_file,
            country=cls.country1,
            local_unit_type=cls.local_unit_type,
            triggered_by=cls.user,
            status=LocalUnitBulkUpload.Status.PENDING,
        )
        runner = BulkUploadHealthData(cls.bulk_upload)
        runner.run()
        cls.bulk_upload.refresh_from_db()
        cls.assertEqual(cls.bulk_upload.status, LocalUnitBulkUpload.Status.FAILED)
        cls.assertIsNotNone(cls.bulk_upload.error_message)
        cls.assertEqual(LocalUnit.objects.count(), 5)
        cls.assertEqual(HealthData.objects.count(), 5)


class TestHealthLocalUnitsPublicList(APITestCase):
    """
    Tests for the public, flattened health local units endpoint: /api/v2/health-local-units/
    Only add new tests; existing code remains untouched.
    """

    def setUp(self):
        super().setUp()
        # Regions and countries
        self.region1 = RegionFactory.create(name=2, label="Asia Pacific")
        self.region2 = RegionFactory.create(name=1, label="Americas")

        self.country1 = CountryFactory.create(name="Nepal", iso3="NPL", region=self.region1)
        self.country2 = CountryFactory.create(name="Philippines", iso3="PHL", region=self.region1)
        self.country3 = CountryFactory.create(name="Brazil", iso3="BRA", region=self.region2)

        # Types
        self.type_health = LocalUnitType.objects.create(code=2, name="Health")
        self.type_admin = LocalUnitType.objects.create(code=1, name="Administrative")

        # Lookups for HealthData
        self.aff = Affiliation.objects.create(code=11, name="Public")
        self.func = Functionality.objects.create(code=21, name="Functional")
        self.ftype = FacilityType.objects.create(code=31, name="Clinic")
        self.phcc = PrimaryHCC.objects.create(code=41, name="Primary")
        self.htype = HospitalType.objects.create(code=51, name="District Hospital")

        # Included: public, not deprecated, type=2 with health
        self.hd1 = HealthDataFactory.create(
            affiliation=self.aff,
            functionality=self.func,
            health_facility_type=self.ftype,
            primary_health_care_center=self.phcc,
            hospital_type=self.htype,
        )
        self.lu1 = LocalUnitFactory.create(
            country=self.country1,
            type=self.type_health,
            health=self.hd1,
            visibility=VisibilityChoices.PUBLIC,
            is_deprecated=False,
            status=LocalUnit.Status.VALIDATED,
            subtype="District Clinic A",
        )

        self.hd2 = HealthDataFactory.create(
            affiliation=self.aff,
            functionality=self.func,
            health_facility_type=self.ftype,
        )
        self.lu2 = LocalUnitFactory.create(
            country=self.country2,
            type=self.type_health,
            health=self.hd2,
            visibility=VisibilityChoices.PUBLIC,
            is_deprecated=False,
            status=LocalUnit.Status.UNVALIDATED,
            subtype="Mobile Clinic",
        )

        # Exclusions
        # - private visibility
        LocalUnitFactory.create(
            country=self.country1,
            type=self.type_health,
            health=HealthDataFactory.create(affiliation=self.aff, functionality=self.func, health_facility_type=self.ftype),
            visibility=VisibilityChoices.MEMBERSHIP,
            is_deprecated=False,
            status=LocalUnit.Status.VALIDATED,
        )
        # - deprecated
        LocalUnitFactory.create(
            country=self.country1,
            type=self.type_health,
            health=HealthDataFactory.create(affiliation=self.aff, functionality=self.func, health_facility_type=self.ftype),
            visibility=VisibilityChoices.PUBLIC,
            is_deprecated=True,
            status=LocalUnit.Status.VALIDATED,
        )
        # - wrong type (admin)
        LocalUnitFactory.create(
            country=self.country1,
            type=self.type_admin,
            health=None,
            visibility=VisibilityChoices.PUBLIC,
            is_deprecated=False,
            status=LocalUnit.Status.VALIDATED,
        )
        # - no health
        LocalUnitFactory.create(
            country=self.country3,
            type=self.type_health,
            health=None,
            visibility=VisibilityChoices.PUBLIC,
            is_deprecated=False,
            status=LocalUnit.Status.VALIDATED,
        )

    def test_list_public_health_local_units(self):
        resp = self.client.get("/api/v2/health-local-units/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 2)
        # Check a few flattened fields exist
        first = resp.data["results"][0]
        self.assertIn("country_name", first)
        self.assertIn("country_iso3", first)
        self.assertEqual(first["type_code"], 2)
        self.assertIn("location", first)
        self.assertIn("affiliation", first)
        self.assertIn("functionality", first)
        self.assertIn("health_facility_type", first)
        # health_facility_type may include image_url; assert at least name exists when present
        if first["health_facility_type"] is not None:
            self.assertIn("name", first["health_facility_type"])

    def test_filters_region_country_iso3_validated_subtype(self):
        # region -> both country1 and country2 are in region1
        resp = self.client.get(f"/api/v2/health-local-units/?region={self.region1.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 2)

        # country
        resp = self.client.get(f"/api/v2/health-local-units/?country={self.country1.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["country_iso3"], "NPL")

        # iso3
        resp = self.client.get("/api/v2/health-local-units/?iso3=PHL")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["country_iso3"], "PHL")

        # validated true
        resp = self.client.get("/api/v2/health-local-units/?validated=true")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["status"], LocalUnit.Status.VALIDATED)

        # validated false
        resp = self.client.get("/api/v2/health-local-units/?validated=false")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["status"], LocalUnit.Status.UNVALIDATED)

        # subtype icontains
        resp = self.client.get("/api/v2/health-local-units/?subtype=mobile")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["subtype"].lower(), "mobile clinic".lower())

        # End of relevant assertions for this test.
