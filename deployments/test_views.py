import json
import datetime
from unittest import mock
from django.core import management

from modeltranslation.utils import build_localized_fieldname
from django.conf import settings

from deployments.factories.project import ProjectFactory
from api.models import Country, District, Region, DisasterType
from main.test_case import APITestCase
from api.models import VisibilityCharChoices


from .models import (
    Project,
    ProgrammeTypes,
    Sectors,
    SectorTags,
    OperationTypes,
    Statuses,
)


def dict_to_string(dict_obj):
    return (
        '-'.join([
            str(dict_obj[key]) for key in sorted(dict_obj.keys())
        ])
    )


class ProjectGetTest(APITestCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.country1 = Country.objects.create(name='country1', iso='XX')
        self.country2 = Country.objects.create(name='country2', iso='YY')

        self.district1 = District.objects.create(name='district1', country=self.country1)
        self.district2 = District.objects.create(name='district2', country=self.country2)

        first = Project.objects.create(
            user=self.user,
            reporting_ns=self.country1,
            name='aaa',
            programme_type=ProgrammeTypes.BILATERAL.value,
            primary_sector=Sectors.WASH.value,
            operation_type=OperationTypes.EMERGENCY_OPERATION.value,
            start_date='2011-11-11',
            end_date='2011-11-11',
            budget_amount=6000,
            status=Statuses.COMPLETED.value,
        )
        first.project_districts.set([self.district1])

        second = Project.objects.create(
            user=self.user,
            reporting_ns=self.country1,
            name='bbb',
            programme_type=ProgrammeTypes.MULTILATERAL.value,
            primary_sector=Sectors.SHELTER.value,
            secondary_sectors=[SectorTags.WASH.value, SectorTags.RCCE.value],
            operation_type=OperationTypes.PROGRAMME.value,
            start_date='2012-12-12',
            end_date='2013-01-01',
            budget_amount=3000,
            status=Statuses.ONGOING.value,
        )
        second.project_districts.set([self.district2])

    def create_project(self, **kwargs):
        project = Project.objects.create(
            user=self.user,
            name='Project Name',
            start_date='2011-11-11',
            end_date='2011-11-11',
            reporting_ns=self.country1,
            programme_type=ProgrammeTypes.BILATERAL.value,
            primary_sector=Sectors.WASH.value,
            operation_type=OperationTypes.PROGRAMME.value,
            status=Statuses.PLANNED.value,
            budget_amount=1000,
            target_total=8000,
            reached_total=1000,
            **kwargs,
        )
        project.project_districts.set(kwargs.pop('project_districts', [self.district1]))
        return project

    def test_1(self):
        self.authenticate(self.user)
        resp = self.client.get('/api/v2/project/')
        self.assertEqual(resp.status_code, 200)

    def test_2(self):
        country2 = Country.objects.get(name='country2')
        district2 = District.objects.get(name='district2')
        self.authenticate(self.user)
        body = {
            'reporting_ns': country2.id,
            'project_country': district2.country.id,
            'project_districts': [district2.id],
            'name': 'CreateMePls',
            'programme_type': ProgrammeTypes.BILATERAL.value,
            'primary_sector': Sectors.WASH.value,
            'secondary_sectors': [Sectors.CEA.value, Sectors.PGI.value],
            'operation_type': OperationTypes.EMERGENCY_OPERATION.value,
            'start_date': '2012-11-12',
            'end_date': '2013-11-13',
            'budget_amount': 7000,
            'target_total': 100,
            'status': Statuses.PLANNED.value,
        }
        resp = self.client.post('/api/v2/project/', body)
        self.assertEqual(resp.status_code, 201, resp.content)

        # Validation Tests

        # Event should be provided if operation type is Emergency Operation and programme type is Multilateral
        body['operation_type'] = OperationTypes.EMERGENCY_OPERATION.value
        body['programme_type'] = ProgrammeTypes.MULTILATERAL.value
        body['event'] = ''
        resp = self.client.post('/api/v2/project/', body)
        self.assertEqual(resp.status_code, 400, resp.content)

        self.assertEqual(len(Project.objects.all()), 3)  # we created 3 projects until now here

    def test_get_projects(self):
        self.authenticate(self.user)
        resp = self.client.get('/api/v2/project/', format='json')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'][0]['name'], 'aaa')
        resp_country_filter = self.client.get('/api/v2/project/?country=YY', format='json')
        self.assertEqual(resp_country_filter.status_code, 200)
        data = json.loads(resp_country_filter.content)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'bbb')
        resp_budget_filter = self.client.get('/api/v2/project/?budget_amount=6000', format='json')
        self.assertEqual(resp_budget_filter.status_code, 200)
        data = json.loads(resp_budget_filter.content)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['name'], 'aaa')

    def test_visibility_project_get(self):
        # Create country for scoping new projects
        country = Country.objects.create(name='new_country', iso='NC')
        public_project = self.create_project(project_country=country, visibility=VisibilityCharChoices.PUBLIC)
        private_project = self.create_project(project_country=country, visibility=VisibilityCharChoices.MEMBERSHIP)
        ifrc_only_project = self.create_project(project_country=country, visibility=VisibilityCharChoices.IFRC)
        # Unauthenticated user
        resp = self.client.get(f'/api/v2/project/?project_country={country.pk}')
        p_ids = [p['id'] for p in resp.json()['results']]
        assert (
            public_project.pk in p_ids and
            private_project.pk not in p_ids and ifrc_only_project.pk not in p_ids
        )
        # Normal user
        self.authenticate(self.user)
        resp = self.client.get(f'/api/v2/project/?project_country={country.pk}')
        p_ids = [p['id'] for p in resp.json()['results']]
        assert (
            public_project.pk in p_ids and private_project.pk in p_ids and
            ifrc_only_project.pk not in p_ids
        )
        # IFRC user
        self.authenticate(self.ifrc_user)
        resp = self.client.get(f'/api/v2/project/?project_country={country.pk}')
        p_ids = [p['id'] for p in resp.json()['results']]
        assert (public_project.pk in p_ids and private_project.pk in p_ids and ifrc_only_project.pk in p_ids)

    def test_regional_project_get(self):
        # Get/Create a region
        # NOTE: If this test fails make sure there no project create for below region
        region, _ = Region.objects.get_or_create(name=1)
        # Remove all the projects for above region
        Project.objects.filter(project_country__region=region).delete()
        # Reporting NS
        rcountry1 = Country.objects.create(name='rcountry1', iso='XX', society_name='country1_sn')
        rcountry2 = Country.objects.create(name='rcountry2', iso='XX', society_name='country2_sn')
        # Create countries
        country1 = Country.objects.create(name='country1', iso='XX', region=region)
        country2 = Country.objects.create(name='country2', iso='XX', region=region)
        # Create districts
        district1 = District.objects.create(name='district1', country=country1)
        district1a = District.objects.create(name='district1aa', country=country1)
        district2 = District.objects.create(name='district2', country=country2)
        district2a = District.objects.create(name='district2a', country=country2)
        # Create new Projects
        for i, pdata in enumerate([
            (
                rcountry1, [district1, district1a],
                ProgrammeTypes.BILATERAL, Sectors.WASH, OperationTypes.PROGRAMME, Statuses.PLANNED,
                6000, 1000, 2),
            (
                rcountry1, [district1],
                ProgrammeTypes.MULTILATERAL, Sectors.WASH, OperationTypes.EMERGENCY_OPERATION, Statuses.ONGOING,
                1000, 2000, 2),
            (
                rcountry1, [district2, district2a],
                ProgrammeTypes.DOMESTIC, Sectors.CEA, OperationTypes.PROGRAMME, Statuses.ONGOING,
                4000, 3000, 1000),
            (
                rcountry1, [district2],
                ProgrammeTypes.BILATERAL, Sectors.HEALTH, OperationTypes.EMERGENCY_OPERATION, Statuses.COMPLETED,
                6000, 9000, 1000),
            (
                rcountry2, [district1, district1a],
                ProgrammeTypes.BILATERAL, Sectors.WASH, OperationTypes.PROGRAMME, Statuses.PLANNED,
                86000, 6000, 3000),
            (
                rcountry2, [district1],
                ProgrammeTypes.MULTILATERAL, Sectors.EDUCATION, OperationTypes.EMERGENCY_OPERATION, Statuses.COMPLETED,
                6000, 5000, 2000),
            (
                rcountry2, [district2, district2a],
                ProgrammeTypes.DOMESTIC, Sectors.DRR, OperationTypes.PROGRAMME, Statuses.PLANNED,
                100, 4000, 2000),
            (
                rcountry2, [district2],
                ProgrammeTypes.BILATERAL, Sectors.MIGRATION, OperationTypes.PROGRAMME, Statuses.COMPLETED,
                2, 1000, 50),
        ]):
            p = Project.objects.create(
                user=self.user,
                name=f'Project {i}',
                start_date='2011-11-11',
                end_date='2011-11-11',
                # Dynamic values
                project_country=pdata[1][0].country,
                reporting_ns=pdata[0],
                programme_type=pdata[2],
                primary_sector=pdata[3],
                operation_type=pdata[4],
                status=pdata[5],
                budget_amount=pdata[6],
                target_total=pdata[7],
                reached_total=pdata[8],
            )
            p.project_districts.set(pdata[1])
        resp = self.client.get(f'/api/v2/region-project/{region.pk}/overview/', format='json')
        self.assertEqual({
            'total_projects': 8,
            'ns_with_ongoing_activities': 1,
            'total_budget': 109102,
            'target_total': 31000,
            'reached_total': 9054,
            'projects_by_status': [
                {'status': 0, 'count': 3},
                {'status': 1, 'count': 2},
                {'status': 2, 'count': 3}
            ]
        }, resp.json())

        resp = self.client.get(f'/api/v2/region-project/{region.pk}/movement-activities/', format='json')
        self.assertEqual({
            'total_projects': 8,
            'countries_count': [
                {
                    'id': country1.id,
                    'name': 'country1',
                    'iso': 'XX',
                    'iso3': None,
                    'projects_count': 4,
                    'planned_projects_count': 2,
                    'ongoing_projects_count': 1,
                    'completed_projects_count': 1
                },
                {
                    'id': country2.id,
                    'name': 'country2',
                    'iso': 'XX',
                    'iso3': None,
                    'projects_count': 4,
                    'planned_projects_count': 1,
                    'ongoing_projects_count': 1,
                    'completed_projects_count': 2
                }
            ],
            'country_ns_sector_count': [
                {
                    'id': country1.id,
                    'name': 'country1',
                    'reporting_national_societies': [
                        {
                            'id': rcountry1.id,
                            'name': 'rcountry1',
                            'sectors': [
                                {'id': 0, 'sector': Sectors.WASH.label, 'count': 2}
                            ]
                        }, {
                            'id': rcountry2.id,
                            'name': 'rcountry2',
                            'sectors': [
                                {'id': 0, 'sector': Sectors.WASH.label, 'count': 1},
                                {'id': 8, 'sector': Sectors.EDUCATION.label, 'count': 1}
                            ]
                        }
                    ]
                }, {
                    'id': country2.id,
                    'name': 'country2',
                    'reporting_national_societies': [
                        {
                            'id': rcountry1.id,
                            'name': 'rcountry1',
                            'sectors': [
                                {'id': 2, 'sector': Sectors.CEA.label, 'count': 1},
                                {'id': 4, 'sector': Sectors.HEALTH.label, 'count': 1}
                            ]
                        }, {
                            'id': rcountry2.id,
                            'name': 'rcountry2',
                            'sectors': [
                                {'id': 3, 'sector': Sectors.MIGRATION.label, 'count': 1},
                                {'id': 5, 'sector': Sectors.DRR.label, 'count': 1}
                            ]
                        }
                    ]
                }
            ],
            'supporting_ns': [
                {'count': 4, 'id': rcountry1.id, 'name': 'rcountry1'},
                {'count': 4, 'id': rcountry2.id, 'name': 'rcountry2'}
            ]
        }, resp.json())

        nation_society_activities_resp = {
            'nodes': sorted(
                [
                    {'id': rcountry1.id, 'type': 'supporting_ns', 'name': 'country1_sn', 'iso': 'XX', 'iso3': None},
                    {'id': rcountry2.id, 'type': 'supporting_ns', 'name': 'country2_sn', 'iso': 'XX', 'iso3': None},
                    {'id': 0, 'type': 'sector', 'name': Sectors.WASH.label},
                    {'id': 2, 'type': 'sector', 'name': Sectors.CEA.label},
                    {'id': 3, 'type': 'sector', 'name': Sectors.MIGRATION.label},
                    {'id': 4, 'type': 'sector', 'name': Sectors.HEALTH.label},
                    {'id': 5, 'type': 'sector', 'name': Sectors.DRR.label},
                    {'id': 8, 'type': 'sector', 'name': Sectors.EDUCATION.label},
                    {'id': country1.id, 'type': 'receiving_ns', 'name': 'country1', 'iso': 'XX', 'iso3': None},
                    {'id': country2.id, 'type': 'receiving_ns', 'name': 'country2', 'iso': 'XX', 'iso3': None}
                ],
                key=lambda item: dict_to_string(item),
            ),
            'links': sorted(
                [
                    {'source': 0, 'target': 2, 'value': 2},
                    {'source': 0, 'target': 3, 'value': 1},
                    {'source': 0, 'target': 5, 'value': 1},
                    {'source': 1, 'target': 2, 'value': 1},
                    {'source': 1, 'target': 4, 'value': 1},
                    {'source': 1, 'target': 6, 'value': 1},
                    {'source': 1, 'target': 7, 'value': 1},
                    {'source': 2, 'target': 8, 'value': 3},
                    {'source': 3, 'target': 9, 'value': 1},
                    {'source': 4, 'target': 9, 'value': 1},
                    {'source': 5, 'target': 9, 'value': 1},
                    {'source': 6, 'target': 9, 'value': 1},
                    {'source': 7, 'target': 8, 'value': 1}
                ],
                key=lambda item: dict_to_string(item),
            ),
        }

        resp = self.client.get(f'/api/v2/region-project/{region.pk}/national-society-activities/', format='json').json()
        self.assertEqual(nation_society_activities_resp, {
            'nodes': sorted(resp['nodes'], key=lambda item: dict_to_string(item)),
            'links': sorted(resp['links'], key=lambda item: dict_to_string(item)),
        })

        resp = self.client.get(f'/api/v2/region-project/national-society-activities/?region={region.pk}', format='json').json()
        self.assertEqual(nation_society_activities_resp, {
            'nodes': sorted(resp['nodes'], key=lambda item: dict_to_string(item)),
            'links': sorted(resp['links'], key=lambda item: dict_to_string(item)),
        })

    def test_project_current_status(self):
        Project.objects.all().delete()
        project = ProjectFactory.create(
            start_date=datetime.date(2012, 11, 12),
            end_date=datetime.date(2012, 12, 13),
            status=Statuses.PLANNED.value,
        )
        self.authenticate()

        patcher = mock.patch('django.utils.timezone.now')
        mock_timezone_now = patcher.start()
        for now, current_status in [
                (datetime.date(2011, 11, 11), Statuses.PLANNED),
                (datetime.date(2012, 11, 12), Statuses.ONGOING),
                (datetime.date(2012, 11, 15), Statuses.ONGOING),
                (datetime.date(2012, 12, 13), Statuses.ONGOING),
                (datetime.date(2012, 12, 14), Statuses.COMPLETED),
        ]:
            mock_timezone_now.return_value.date.return_value = now
            management.call_command('update_project_status')
            response = self.client.get(f'/api/v2/project/{project.id}/')
            self.assert_200(response)
            self.assertEqual(response.data['status_display'], str(current_status))
        patcher.stop()


class TranslationTest(APITestCase):
    def test_translation_api_behaviour(self):
        """
        NOTE: This test covers for API behaviour for translation mixin serializer
        TODO: Use model with more then one field used for translation
        """
        country = Country.objects.create(name='country', iso='YY')
        district = District.objects.create(name='district', country=country)
        disaster_names = {
            'en': 'Disaster 1 (EN)',
            'es': 'Disaster 1 (ES)',
            'fr': 'Disaster 1 (FR)',
            'ar': 'Disaster 1 (AR)',
        }
        names = {
            'en': 'Project 1 (EN)',
            'es': 'Project 1 (ES)',
            'fr': 'Project 1 (FR)',
            'ar': 'Project 1 (AR)',
        }

        disaster_type = DisasterType()
        for lang, _ in settings.LANGUAGES:
            setattr(disaster_type, build_localized_fieldname('name', lang), disaster_names[lang])
        disaster_type.save()

        self.authenticate(self.user)

        # Using both header and GET Param
        for using in ['header']:
            for current_language, _ in settings.LANGUAGES:
                body = {
                    'reporting_ns': country.id,
                    'project_country': district.country.id,
                    'dtype': disaster_type.pk,
                    'project_districts': [district.id],
                    'name': names[current_language],
                    'programme_type': ProgrammeTypes.BILATERAL.value,
                    'primary_sector': Sectors.WASH.value,
                    'secondary_sectors': [Sectors.CEA.value, Sectors.PGI.value],
                    'operation_type': OperationTypes.EMERGENCY_OPERATION.value,
                    'start_date': '2012-11-12',
                    'end_date': '2013-11-13',
                    'budget_amount': 7000,
                    'target_total': 100,
                    'status': Statuses.PLANNED.value,
                }

                # POST (Creation)
                with self.capture_on_commit_callbacks(execute=True):
                    # https://docs.djangoproject.com/en/3.0/topics/testing/tools/#setting-the-language
                    resp = self.client.post('/api/v2/project/', body, HTTP_ACCEPT_LANGUAGE=current_language)

                # NOTE: non-safe methods are not allowd for non english language
                if current_language == settings.LANGUAGE_CODE:
                    self.assertEqual(resp.status_code, 201, resp.content)
                else:
                    self.assertEqual(resp.status_code, 405, resp.content)

                project_id = resp.json().get('id')
                if project_id is None:
                    continue

                # GET
                for lang, _ in settings.LANGUAGES:
                    resp = self.client.get(f'/api/v2/project/{project_id}/', HTTP_ACCEPT_LANGUAGE=lang)
                    self.assertEqual(resp.status_code, 200, resp.content)
                    resp_body = resp.json()
                    if lang == current_language:
                        assert resp_body['name'] == names[current_language], \
                            f"Name ({lang}): <{resp_body['name']}> should be <{names[current_language]}>"
                    else:
                        translated_text = self.aws_translator._fake_translation(names[current_language], lang, current_language)
                        assert resp_body['name'] == translated_text,\
                            f"Name ({lang}): should be <{translated_text}> instead of <{resp_body['name']}>"
                    # Test Nested Field Disaster Type Name
                    assert resp_body['dtype_detail']['name'] == disaster_names[lang], \
                        f"Name ({lang}): <{resp_body['dtype_detail']['name']}> should be <{disaster_names[lang]}>"

                # Update (This doesn't reset other language)
                body['name'] += ''
                with self.capture_on_commit_callbacks(execute=True):
                    resp = self.client.put(f'/api/v2/project/{project_id}/', body, HTTP_ACCEPT_LANGUAGE=current_language)
                self.assertEqual(resp.status_code, 200, resp.content)

                # non current language field should not be None
                project = Project.objects.get(pk=project_id)
                for lang, _ in settings.LANGUAGES:
                    value = getattr(project, build_localized_fieldname('name', lang))
                    if lang == current_language:
                        assert value == body['name'], f"Name ({lang}): <{value}> should be {body['name']}"
                    else:
                        assert value is not None, f"Name ({lang}): value shouldn't be None"

                # Update (Reset other language) (Without onCommit Trigger by not using self.capture_on_commit_callbacks)
                # This way the language field are reset but auto translation work is reverted back i.e reset is preserved
                body['name'] += ' Changed'
                resp = self.client.put(f'/api/v2/project/{project_id}/', body, HTTP_ACCEPT_LANGUAGE=current_language)
                self.assertEqual(resp.status_code, 200, resp.content)

                # non current language field should be None
                project = Project.objects.get(pk=project_id)
                for lang, _ in settings.LANGUAGES:
                    value = getattr(project, build_localized_fieldname('name', lang))
                    if lang == current_language:
                        assert value == body['name'], f"Name ({lang}): <{value}> should be {body['name']}"
                    else:
                        assert value is None, f"Name ({lang}): <{value}> should be None"

                # Again Update (With onCommit Trigger: Mock Translation)
                body['name'] += ' Again Changed'
                with self.capture_on_commit_callbacks(execute=True):
                    resp = self.client.put(f'/api/v2/project/{project_id}/', body, HTTP_ACCEPT_LANGUAGE=current_language)
                self.assertEqual(resp.status_code, 200, resp.content)

                # non current language field should be None
                project = Project.objects.get(pk=project_id)
                for lang, _ in settings.LANGUAGES:
                    value = getattr(project, build_localized_fieldname('name', lang))
                    if lang == current_language:
                        assert value == body['name'], f"Name ({lang}): <{value}> should be {body['name']}"
                    else:
                        assert value is not None, f"Name ({lang}): <{value}> should not be None"
