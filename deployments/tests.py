import pdb

import pydash

import json

from main.test_case import SnapshotTestCase, APITestCase
from deployments.factories.user import UserFactory
from deployments.factories.project import ProjectFactory
from api.factories import country, district
import api.models as models
from deployments.models import Project, VisibilityCharChoices, SectorTags

from .factories.personnel import PersonnelFactory
from deployments.factories.emergency_project import (
    EmergencyProjectActivityFactory,
    EmergencyProjectFactory,
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

#tmply        # check response
#tmply        self.assert_200(response)
#tmply        self.assertMatchSnapshot(json.loads(response.content))
#tmply
#tmply    def test_project_list_one(self):
#tmply        # create instance
#tmply        ProjectFactory.create(visibility=VisibilityCharChoices.PUBLIC)
#tmply
#tmply        # submit list request
#tmply        response = self.client.get("/api/v2/project/")
#tmply
#tmply        # check response
#tmply        self.assert_200(response)
#tmply        self.assertMatchSnapshot(json.loads(response.content))
#tmply
#tmply    def test_project_list_two(self):
#tmply        # create instances
#tmply        ProjectFactory.create_batch(2, visibility=VisibilityCharChoices.PUBLIC)
#tmply
#tmply        # submit list request
#tmply        response = self.client.get("/api/v2/project/")
#tmply
#tmply        # check response
#tmply        self.assert_200(response)
#tmply        self.assertMatchSnapshot(json.loads(response.content))
#tmply
#tmply    def test_project_create(self):
#tmply        # authenticate
#tmply        new_user = UserFactory.create()
#tmply        self.authenticate(new_user)
#tmply
#tmply        # create project
#tmply        new_project_name = "Mock Project for Create API Test"
#tmply        new_project = ProjectFactory.stub(
#tmply            name=new_project_name,
#tmply            visibility=VisibilityCharChoices.PUBLIC,
#tmply            user=new_user,
#tmply        )
#tmply        new_country = country.CountryFactory()
#tmply        new_district = district.DistrictFactory(country=new_country)
#tmply        new_project = pydash.omit(
#tmply            new_project,
#tmply            [
#tmply                "user",
#tmply                "reporting_ns",
#tmply                "project_country",
#tmply                "event",
#tmply                "dtype",
#tmply                "regional_project",
#tmply            ],
#tmply        )
#tmply        new_project["reporting_ns"] = new_country.id
#tmply        new_project["project_country"] = new_country.id
#tmply        new_project["project_districts"] = [new_district.id]
#tmply
#tmply        # submit create request
#tmply        response = self.client.post("/api/v2/project/", new_project, format='json')
#tmply
#tmply        # check response
#tmply        self.assert_201(response)
#tmply        self.assertMatchSnapshot(json.loads(response.content))
#tmply        self.assertTrue(Project.objects.get(name=new_project_name))
#tmply
#tmply    def test_project_read(self):
#tmply        # create instance
#tmply        new_project = ProjectFactory.create(
#tmply            visibility=VisibilityCharChoices.PUBLIC
#tmply        )
#tmply
#tmply        # submit read request
#tmply        response = self.client.get(f"/api/v2/project/{new_project.pk}/")
#tmply
#tmply        # check response
#tmply        self.assert_200(response)
#tmply        self.assertMatchSnapshot(json.loads(response.content))
#tmply
#tmply    def test_project_update(self):
#tmply        # create instance
#tmply        new_project = ProjectFactory.create(
#tmply            visibility=VisibilityCharChoices.PUBLIC
#tmply        )
#tmply
#tmply        # authenticate
#tmply        self.authenticate()
#tmply
#tmply        new_project = pydash.omit(
#tmply            new_project,
#tmply            ["_state", "modified_at", "user", "event", "dtype", "regional_project"],
#tmply        )
#tmply        # update project name
#tmply        new_project_name = "Mock Project for Update API Test"
#tmply        new_country = country.CountryFactory()
#tmply        new_district = district.DistrictFactory(country=new_country)
#tmply        new_project["name"] = new_project_name
#tmply        new_project["reporting_ns"] = new_country.id
#tmply        new_project["project_country"] = new_country.id
#tmply        new_project["event"] = new_project["event_id"]
#tmply        new_project["project_districts"] = [new_district.id]
#tmply
#tmply        # submit update request
#tmply        response = self.client.put(f"/api/v2/project/{new_project['id']}/", new_project, format='json')
#tmply
#tmply        # check response
#tmply        self.assert_200(response)
#tmply        self.assertMatchSnapshot(json.loads(response.content))
#tmply        self.assertTrue(Project.objects.get(name=new_project_name))
#tmply
#tmply    def test_project_delete(self):
#tmply        # create instance
#tmply        new_project = ProjectFactory.create(
#tmply            visibility=VisibilityCharChoices.PUBLIC
#tmply        )
#tmply
#tmply        # authenticate
#tmply        self.authenticate()
#tmply
#tmply        # submit delete request
#tmply        response = self.client.delete("/api/v2/project/{}/".format(new_project.pk))
#tmply
#tmply        # check response
#tmply        self.assert_204(response)
#tmply        self.assertMatchSnapshot(response.content)
#tmply        self.assertFalse(Project.objects.count())
#tmply
#tmply    def test_personnel_csv_api(self):
#tmply        [PersonnelFactory() for i in range(10)]
#tmply        # originally it was so rich. TODO: instead of Personnel fields manually create new ones.
#tmply        # country_from,country_to,deployment.comments,deployment.country_deployed_to.id,deployment.country_deployed_to.iso,deployment.country_deployed_to.iso3,deployment.country_deployed_to.name,deployment.country_deployed_to.society_name,deployment.event_deployed_to,deployment.id,end_date,id,is_active,molnix_id,molnix_language,molnix_modality,molnix_operation,molnix_region,molnix_role_profile,molnix_scope,molnix_sector,name,role,start_date,type\r
#tmply        # ,,,1,gw,wMq,country-OhbVrpoiVgRVIfLBcbfnoGMbJmTPSIAoCLrZaWZkSBvrjnWvgf,society-name-ZcUDIhyfJsONxKmTecQoXsfogyrDOxkxwnQrSRPeMOkIUpkDyr,,1,,1,True,,,,,,,,,,,,\r
#tmply        # ,,,2,Eb,NJu,country-VAlmiYIxHGrkqEZsVvZhDejWoRURzZJxfYzaqIhDxRVRqLyOxg,society-name-NoPeODStPAhicctFhgpIiyDxQVSIALVUjAPgFNArcSxnCCpxgR,,2,,2,True,,,,,,,,,,,,\r
#tmply        # ,,,3,Os,xNo,country-RWmlNOzBGufzQgliEupaqypCWrvtLUKaqPxSpdQhDtkzRGTXtS,society-name-oiEjDVMxASJEWIZQnWpRWMYfHCHTxeKhdJGmKIjkuHChRnTLFf,,3,,3,True,,,,,,,,,,,,\r
#tmply        # ,,,4,TS,Mcn,country-GiOzeLKdBQipsquZzSVuuCroemiXXLgjgkCDuAhIwXnCtDqhfk,society-name-ujfTpwzGdRtqlbzCJVJpgDgZYihadXoimzxROPfLLqebemPCZi,,4,,4,True,,,,,,,,,,,,\r
#tmply        # ,,,5,Pe,VRj,country-PNNpcRuyYhyqIUsbHXxGZGCFcsPmuGfgkXIIaOenQOXnRBgnIS,society-name-bDTvcfedlYqJeKoqAyCOzBubyRhIaPUNeWVLcSewGgsYRtMfsW,,5,,5,True,,,,,,,,,,,,\r
#tmply        # ,,,6,oB,sYz,country-gMPtcUZKyfXdXvwBAhXoVPMaOXOydtHcuIKjuGSojdRUzCWMKG,society-name-jivfEKVdJzqfzGBXSiWiEJmFzPKmJNVHpperXBuRKfhQABxwmu,,6,,6,True,,,,,,,,,,,,\r
#tmply        # ,,,7,Zm,BvZ,country-YUczhnZPQHDRIjVLoecVjFPbENcpSPialOdtYgDNkLeghFMZNo,society-name-VRzuhRKIiuYnWcLlvehrjWAkSxJkCpLcigYONyXkbFfaalfTPL,,7,,7,True,,,,,,,,,,,,\r
#tmply        # ,,,8,TH,BXD,country-MRAYuCEViqlRLuZsmfAxlzyKobbJPNOofDmqSkdzNBMqjfxkKh,society-name-RFhoTnmYrsVFyiBnMnsURmAlAYjbsqpNCpxLRPDfaEiuSzRnTy,,8,,8,True,,,,,,,,,,,,\r
#tmply        # ,,,9,ax,aew,country-BwmmOmYevmQESSDMSvLKvNtAvkgDYcFoaOoSoDNnpEVXvZVynz,society-name-bJhjsCmOLWxcbmmsloqUlvJplmblqgbRiyPYhvntDpxZxQkHZN,,9,,9,True,,,,,,,,,,,,\r
#tmply        # ,,,10,bM,per,country-niMJnLwriUNBeJqqyPkzDfqRBSjIneOUrOSPmTxKQPGMkAjuYB,society-name-hIhRJAevOfxvXrjZoragyoygYhlHUtLZFgHwSKsJrMgdkuWylw,,10,,10,True,,,,,,,,,,,,\r
#tmply
#tmply        url = '/api/v2/personnel/?format=csv'
#tmply        # Also unaunthenticated user can use this, but without names:
#tmply        # resp = self.client.get(url)
#tmply        # self.assert_401(resp)
#tmply
#tmply        self.authenticate()
#tmply        resp = self.client.get(url)
#tmply        self.assert_200(resp)
#tmply        self.assertMatchSnapshot(resp.content.decode('utf-8'))
#tmply
#tmply    def test_project_csv_api(self):
#tmply        _country = country.CountryFactory()
#tmply        district1 = district.DistrictFactory(country=_country)
#tmply        district2 = district.DistrictFactory(country=_country)
#tmply        ProjectFactory.create_batch(
#tmply            10,
#tmply            project_districts=[district1, district2],
#tmply            secondary_sectors=[SectorTags.WASH, SectorTags.PGI],
#tmply            visibility=VisibilityCharChoices.PUBLIC
#tmply        )
#tmply
#tmply        url = '/api/v2/project/?format=csv'
#tmply        resp = self.client.get(url)
#tmply        self.assert_200(resp)
#tmply        self.assertMatchSnapshot(resp.content.decode('utf-8'))
#tmply
#tmply    def test_global_project_api(self):
#tmply        country_1 = country.CountryFactory()
#tmply        country_2 = country.CountryFactory()
#tmply        ns_1 = country.CountryFactory()
#tmply        ns_2 = country.CountryFactory()
#tmply        c1_district1 = district.DistrictFactory(country=country_1)
#tmply        c1_district2 = district.DistrictFactory(country=country_1)
#tmply        c2_district1 = district.DistrictFactory(country=country_2)
#tmply        c2_district2 = district.DistrictFactory(country=country_2)
#tmply        [
#tmply            ProjectFactory.create_batch(
#tmply                2,
#tmply                project_districts=project_districts,
#tmply                secondary_sectors=secondary_sectors,
#tmply                visibility=VisibilityCharChoices.PUBLIC,
#tmply            )
#tmply            for project_districts, secondary_sectors in [
#tmply                ([c1_district1, c1_district2], [SectorTags.WASH, SectorTags.PGI]),
#tmply                ([c1_district1, c1_district2], [SectorTags.WASH, SectorTags.MIGRATION]),
#tmply                ([c2_district1, c2_district2], [SectorTags.LIVELIHOODS_AND_BASIC_NEEDS, SectorTags.PGI]),
#tmply                ([c2_district1, c2_district2], [SectorTags.INTERNAL_DISPLACEMENT, SectorTags.RECOVERY]),
#tmply            ]
#tmply            for ns in [ns_1, ns_2]
#tmply        ]
#tmply
#tmply        url = '/api/v2/global-project/overview/'
#tmply        resp = self.client.get(url)
#tmply        self.assert_200(resp)
#tmply        self.assertMatchSnapshot(resp.json())
#tmply
#tmply        url = '/api/v2/global-project/ns-ongoing-projects-stats/'
#tmply        resp = self.client.get(url)
#tmply        self.assert_200(resp)
#tmply        self.assertMatchSnapshot(resp.json())


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
