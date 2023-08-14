import pydash
import json

from main.test_case import SnapshotTestCase, APITestCase
from deployments.factories.user import UserFactory
from deployments.factories.project import SectorFactory, SectorTagFactory, ProjectFactory
from api.factories import country, district
import api.models as models
from deployments.models import Project, VisibilityCharChoices, SectorTag

from .factories.personnel import PersonnelFactory
from deployments.factories.emergency_project import (
    EmergencyProjectActivityFactory,
    EmergencyProjectActivityActionFactory,
    EmergencyProjectActivitySectorFactory,
    EruFactory,
)
from api.factories.event import EventFactory
from deployments.models import EmergencyProject, EmergencyProjectActivity


class TestProjectAPI(SnapshotTestCase):
    def test_project_list_zero(self):
        # submit list request
        response = self.client.get("/api/v2/project/")

        # check response
        self.assert_200(response)
        self.assertMatchSnapshot(json.loads(response.content))

    def test_project_list_one(self):
        # create instance
        sct = SectorFactory()
        ProjectFactory.create(visibility=VisibilityCharChoices.PUBLIC, primary_sector=sct)

        # submit list request
        response = self.client.get("/api/v2/project/")

        # check response
        self.assert_200(response)
        self.assertMatchSnapshot(json.loads(response.content))

    def test_project_list_two(self):
        # create instances
        sct = SectorFactory()
        ProjectFactory.create_batch(2, visibility=VisibilityCharChoices.PUBLIC, primary_sector=sct)

        # submit list request
        response = self.client.get("/api/v2/project/")

        # check response
        self.assert_200(response)
        self.assertMatchSnapshot(json.loads(response.content))

    def test_project_create(self):
        # authenticate
        new_user = UserFactory.create()
        self.authenticate(new_user)

        # create project
        new_project_name = "Mock Project for Create API Test"
        new_project = ProjectFactory.stub(
            name=new_project_name,
            visibility=VisibilityCharChoices.PUBLIC,
            user=new_user,
        )
        new_country = country.CountryFactory()
        new_district = district.DistrictFactory(country=new_country)
        new_sector = SectorFactory()
        new_sector1 = SectorTagFactory()
        new_sector2 = SectorTagFactory()
        new_project = pydash.omit(
            new_project,
            [
                "user",
                "reporting_ns",
                "project_country",
                "event",
                "dtype",
                "regional_project",
            ],
        )
        new_project["reporting_ns"] = new_country.id
        new_project["project_country"] = new_country.id
        new_project["project_districts"] = [new_district.id]
        new_project["primary_sector"] = new_sector.id
        new_project["secondary_sectors"] = [new_sector1.id, new_sector2.id]

        # submit create request
        response = self.client.post("/api/v2/project/", new_project, format='json')

        # check response
        self.assert_201(response)
        self.assertMatchSnapshot(json.loads(response.content))
        self.assertTrue(Project.objects.get(name=new_project_name))

    def test_project_read(self):
        # create instance
        sct = SectorFactory()
        new_project = ProjectFactory.create(
            visibility=VisibilityCharChoices.PUBLIC,
            primary_sector=sct
        )

        # submit read request
        response = self.client.get(f"/api/v2/project/{new_project.pk}/")

        # check response
        self.assert_200(response)
        self.assertMatchSnapshot(json.loads(response.content))

    def test_project_update(self):
        # create instance
        sct = SectorFactory()
        new_project = ProjectFactory.create(
            visibility=VisibilityCharChoices.PUBLIC,
            primary_sector=sct
        )

        # authenticate
        self.authenticate()

        new_project = pydash.omit(
            new_project,
            ["_state", "modified_at", "user", "event", "dtype", "regional_project"],
        )
        # update project name
        new_project_name = "Mock Project for Update API Test"
        new_country = country.CountryFactory()
        new_district = district.DistrictFactory(country=new_country)
        new_project["name"] = new_project_name
        new_project["reporting_ns"] = new_country.id
        new_project["project_country"] = new_country.id
        new_project["event"] = new_project["event_id"]
        new_project["project_districts"] = [new_district.id]
        new_project["primary_sector"] = sct.id

        # submit update request
        response = self.client.put(f"/api/v2/project/{new_project['id']}/", new_project, format='json')

        # check response
        self.assert_200(response)
        self.assertMatchSnapshot(json.loads(response.content))
        self.assertTrue(Project.objects.get(name=new_project_name))

    def test_project_delete(self):
        # create instance
        sct = SectorFactory()
        new_project = ProjectFactory.create(
            visibility=VisibilityCharChoices.PUBLIC,
            primary_sector=sct
        )

        # authenticate
        self.authenticate()

        # submit delete request
        response = self.client.delete("/api/v2/project/{}/".format(new_project.pk))

        # check response
        self.assert_204(response)
        self.assertMatchSnapshot(response.content)
        self.assertFalse(Project.objects.count())

    def test_personnel_csv_api(self):
        [PersonnelFactory() for i in range(10)]
        # originally it was so rich. TODO: instead of Personnel fields manually create new ones.
        # country_from,country_to,deployment.comments,deployment.country_deployed_to.id,deployment.country_deployed_to.iso,deployment.country_deployed_to.iso3,deployment.country_deployed_to.name,deployment.country_deployed_to.society_name,deployment.event_deployed_to,deployment.id,end_date,id,is_active,molnix_id,molnix_language,molnix_modality,molnix_operation,molnix_region,molnix_role_profile,molnix_scope,molnix_sector,name,role,start_date,type\r
        # ,,,1,gw,wMq,country-OhbVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgf,society-name-ZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUpkDyr,,1,,1,True,,,,,,,,,,,,\r
        # ,,,2,Eb,NJu,country-VAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOxg,society-name-NoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgR,,2,,2,True,,,,,,,,,,,,\r
        # ,,,3,Os,xNo,country-RWmlNOzBGufzQgliEupaqypCWrvtLUKaqPxSpdQhDtkzRGTXtS,society-name-oiEjDVMxASJEWIZQnWpRWMYfHCHTxeKhdJGmKIjkuHChRnTLFf,,3,,3,True,,,,,,,,,,,,\r
        # ,,,4,TS,Mcn,country-GiOzeLKdBQipsquZzSVuuCroemiXXLgjgkCDuAhIwXnCtDqhfk,society-name-ujfTpwzGdRtqlbzCJVJpgDgZYihadXoimzxROPfLLqebemPCZi,,4,,4,True,,,,,,,,,,,,\r
        # ,,,5,Pe,VRj,country-PNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnIS,society-name-bDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsW,,5,,5,True,,,,,,,,,,,,\r
        # ,,,6,oB,sYz,country-gMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGSojdRUzCWMKG,society-name-jivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmu,,6,,6,True,,,,,,,,,,,,\r
        # ,,,7,Zm,BvZ,country-YUczhnZPQHDRIjVLoecVjFPbENcpSPialOdtYgDNkLeghFMZNo,society-name-VRzuhRKIiuYnWcLlvehrjWAkSxJkCpLcigYONyXkbFfaalfTPL,,7,,7,True,,,,,,,,,,,,\r
        # ,,,8,TH,BXD,country-MRAYuCEViqlRLuZsmfAxlzyKobbJPNOofDmqSkdzNBMqjfxkKh,society-name-RFhoTnmYrsVFyiBnMnsURmAlAYjbsqpNCpxLRPDfaEiuSzRnTy,,8,,8,True,,,,,,,,,,,,\r
        # ,,,9,ax,aew,country-BwmmOmYevmQESSDMSvLKvNtAvkgDYcFoaOoSoDNnpEVXvZVynz,society-name-bJhjsCmOLWxcbmmsloqUlvJplmblqgbRiyPYhvntDpxZxQkHZN,,9,,9,True,,,,,,,,,,,,\r
        # ,,,10,bM,per,country-niMJnLwriUNBeJqqyPkzDfqRBSjIneOUrOSPmTxKQPGMkAjuYB,society-name-hIhRJAevOfxvXrjZoragyoygYhlHUtLZFgHwSKsJrMgdkuWylw,,10,,10,True,,,,,,,,,,,,\r

        url = '/api/v2/personnel/?format=csv'
        # Also unaunthenticated user can use this, but without names:
        # resp = self.client.get(url)
        # self.assert_401(resp)

        self.authenticate()
        resp = self.client.get(url)
        self.assert_200(resp)
        self.assertMatchSnapshot(resp.content.decode('utf-8'))

    def test_project_csv_api(self):
        _country = country.CountryFactory()
        sct = SectorFactory()
        sct_1 = SectorTagFactory()
        sct_2 = SectorTagFactory()
        district1 = district.DistrictFactory(country=_country)
        district2 = district.DistrictFactory(country=_country)
        ProjectFactory.create_batch(
            10,
            project_districts=[district1, district2],
            primary_sector=sct,
            secondary_sectors=[sct_1, sct_2],
            visibility=VisibilityCharChoices.PUBLIC
        )

        url = '/api/v2/project/?format=csv'
        resp = self.client.get(url)
        self.assert_200(resp)
        self.assertMatchSnapshot(resp.content.decode('utf-8'))

    def test_global_project_api(self):
        country_1 = country.CountryFactory()
        country_2 = country.CountryFactory()
        ns_1 = country.CountryFactory()
        ns_2 = country.CountryFactory()
        c1_district1 = district.DistrictFactory(country=country_1)
        c1_district2 = district.DistrictFactory(country=country_1)
        c2_district1 = district.DistrictFactory(country=country_2)
        c2_district2 = district.DistrictFactory(country=country_2)
        sct = SectorFactory()
        sct_1 = SectorTagFactory()
        sct_2 = SectorTagFactory()
        sct_3 = SectorTagFactory()
        sct_4 = SectorTagFactory()
        [
            ProjectFactory.create_batch(
                2,
                primary_sector=sct,
                project_districts=project_districts,
                visibility=VisibilityCharChoices.PUBLIC,
            )
            for project_districts, secondary_sectors in [
                ([c1_district1, c1_district2], [sct_1, sct_2]),
                ([c1_district1, c1_district2], [sct_3, sct_4]),
                ([c2_district1, c2_district2], [sct_1, sct_3]),
                ([c2_district1, c2_district2], [sct_2, sct_4]),
            ]
            for ns in [ns_1, ns_2]
        ]

        url = '/api/v2/global-project/overview/'
        resp = self.client.get(url)
        self.assert_200(resp)
        self.assertMatchSnapshot(resp.json())

        url = '/api/v2/global-project/ns-ongoing-projects-stats/'
        resp = self.client.get(url)
        self.assert_200(resp)
        self.assertMatchSnapshot(resp.json())


class TestEmergencyProjectAPI(APITestCase):
    fixtures = ['emergency_project_activity_actions.json']

    def test_emergency_project(self):
        supplies = {
            '2': 100,
            '1': 1,
            '4': 3
        }
        EmergencyProjectActivityFactory.create_batch(5, supplies=supplies)
        url = '/api/v2/emergency-project/'
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)
        self.assertEqual(len(response.data['results']), 5)

    def test_emergency_project_create(self):
        old_emergency_project_count = EmergencyProject.objects.count()
        old_emergency_project_activity_count = EmergencyProjectActivity.objects.count()
        country1 = models.Country.objects.create(name='abc')
        country2 = models.Country.objects.create(name='xyz')
        district1 = models.District.objects.create(name='test district1', country=country1)
        district2 = models.District.objects.create(name='test district2', country=country1)
        sector = EmergencyProjectActivitySectorFactory.create()
        action = EmergencyProjectActivityActionFactory.create()
        event = EventFactory.create(
            countries=[country1.id, country2.id],
            districts=[district1.id, district2.id]
        )
        reporting_ns = models.Country.objects.create(name='ne')
        deployed_eru = EruFactory.create()
        data = {
            'title': "Emergency title",
            'event': event.id,
            'districts': [district1.id, district2.id],
            'reporting_ns': reporting_ns.id,
            'reporting_ns_contact_email': None,
            'reporting_ns_contact_name': None,
            'reporting_ns_contact_role': None,
            'status': EmergencyProject.ActivityStatus.ON_GOING,
            'activity_lead': EmergencyProject.ActivityLead.NATIONAL_SOCIETY,
            'start_date': '2022-01-01',
            'deployed_eru': deployed_eru.id,
            'country': country1.id,
            "activities": [
                {
                    "sector": sector.id,
                    "action": action.id,
                    "people_count": 2,
                    "male": 3,
                    "female": 5,
                    "people_households": EmergencyProjectActivity.PeopleHouseholds.PEOPLE,
                    "custom_supplies": {
                        "test_supplies": 23,
                        "test_world": 34,
                        "test_emergency": 56
                    },
                    "points": []
                },
            ]
        }
        url = '/api/v2/emergency-project/'
        self.authenticate()
        response = self.client.post(url, data=data, format='json')
        self.assert_201(response)
        self.assertEqual(EmergencyProject.objects.count(), old_emergency_project_count + 1)
        self.assertEqual(EmergencyProjectActivity.objects.count(), old_emergency_project_activity_count + 1)
