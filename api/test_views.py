import json

from django.contrib.auth.models import User
from django.conf import settings

from main.test_case import APITestCase, SnapshotTestCase
import api.models as models

from api.factories.event import (
    EventFactory,
    EventFeaturedDocumentFactory,
    EventLinkFactory,
    AppealFactory
)


class AuthTokenTest(APITestCase):
    def setUp(self):
        user = User.objects.create(username='jo')
        user.set_password('12345678')
        user.save()

    def test_get_auth(self):
        body = {
            'username': 'jo',
            'password': '12345678',
        }
        headers = {'CONTENT_TYPE': 'application/json'}
        response = self.client.post('/get_auth_token', body, format='json', headers=headers).json()
        self.assertIsNotNone(response.get('token'))
        self.assertIsNotNone(response.get('expires'))


class EventSnaphostTest(SnapshotTestCase):
    def test_event_featured_document_api(self):
        event = EventFactory()
        EventFeaturedDocumentFactory.create_batch(5, event=event)
        resp = self.client.get(f'/api/v2/event/{event.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertMatchSnapshot(json.loads(resp.content))

    def test_event_link_api(self):
        event = EventFactory()
        EventLinkFactory.create_batch(5, event=event)
        resp = self.client.get(f'/api/v2/event/{event.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertMatchSnapshot(json.loads(resp.content))


class SituationReportTypeTest(APITestCase):

    fixtures = ['DisasterTypes']

    def test_sit_rep_types(self):
        type1 = models.SituationReportType.objects.create(type='Lyric')
        type2 = models.SituationReportType.objects.create(type='Epic')
        dtype1 = models.DisasterType.objects.get(pk=1)
        event1 = models.Event.objects.create(name='disaster1', summary='test disaster1', dtype=dtype1)

        models.SituationReport.objects.create(name='test1', event=event1, type=type1, visibility=3)
        models.SituationReport.objects.create(name='test2', event=event1, type=type2, visibility=3)
        models.SituationReport.objects.create(name='test3', event=event1, type=type2, visibility=3)

        # Filter by event
        response = self.client.get('/api/v2/situation_report/?limit=100&event=%s' % event1.id)
        self.assertEqual(response.status_code, 200)
        count = response.json()['count']
        self.assertEqual(count, 3)

        # Filter by event and type
        response = self.client.get('/api/v2/situation_report/?limit=100&event=%s&type=%s' % (event1.id, type2.id))
        self.assertEqual(response.status_code, 200)
        count = response.json()['count']
        self.assertEqual(count, 2)


class FieldReportTest(APITestCase):

    fixtures = ['DisasterTypes', 'Actions']

    def test_create_and_update(self):
        user = User.objects.create(username='jo')
        region = models.Region.objects.create(name=1)
        country1 = models.Country.objects.create(name='abc', region=region)
        country2 = models.Country.objects.create(name='xyz')
        source1 = models.SourceType.objects.create(name="source1")
        source2 = models.SourceType.objects.create(name="source2")
        body = {
            'countries': [country1.id, country2.id],
            'dtype': 7,
            'summary': 'test',
            'description': 'this is a test description',
            'bulletin': '3',
            'num_assisted': 100,
            'visibility': models.VisibilityChoices.IFRC,
            'sources': [
                {'stype': source1.id, 'spec': 'A source'},
                {'stype': source2.id, 'spec': 'Another source'},
            ],
            'actions_taken': [
                {'organization': 'NTLS', 'summary': 'actions taken', 'actions': ['37', '30', '39']},
            ],
            'dref': '2',
            'appeal': '1',
            'contacts': [
                {'ctype': 'Originator', 'name': 'jo', 'title': 'head', 'email': '123'}
            ],
            'user': user.id,
        }
        self.client.force_authenticate(user=user)
        response = self.client.post('/api/v2/field-report/', body, format='json').json()
        old_respone_id = response['id']
        created = models.FieldReport.objects.get(pk=old_respone_id)
        print(created.id, "~~~~~~~~~~~~~~~~~~~~~~~~")

        self.assertEqual(created.countries.count(), 2)
        # one region attached automatically
        self.assertEqual(created.regions.count(), 1)

        self.assertEqual(created.sources.count(), 2)
        source_types = list([source.stype.name for source in created.sources.all()])
        self.assertTrue('source1' in source_types)
        self.assertTrue('source2' in source_types)

        self.assertEqual(created.actions_taken.count(), 1)
        actions = list([action.id for action in created.actions_taken.first().actions.all()])
        self.assertTrue(37 in actions)
        self.assertTrue(30 in actions)
        self.assertTrue(39 in actions)

        self.assertEqual(created.contacts.count(), 1)
        self.assertEqual(created.visibility, models.VisibilityChoices.IFRC)
        self.assertEqual(created.dtype.id, 7)
        self.assertEqual(created.summary, 'test')
        # Translated field test
        self.assertEqual(created.summary_en, 'test')

        # created an emergency automatically
        self.assertEqual(created.event.name, 'test')
        # event_pk = created.event.id

        # body['countries'] = [country2.id]
        # body['summary'] = 'test [updated]'
        # body['sources'] = [
        #     {'stype': source1.id, 'spec': 'something'},
        #     {'stype': source2.id, 'spec': 'other'},
        # ]
        # body['actions_taken'] = []
        # body['visibility'] = models.VisibilityChoices.PUBLIC
        # self.client.force_authenticate(user=user)
        # response = self.client.patch(f'/api/v2/field-report/{old_respone_id}/', body)
        # print(response.content)
        # updated = models.FieldReport.objects.get(pk=old_respone_id)

        # self.assertEqual(updated.countries.count(), 1)
        # self.assertEqual(updated.countries.first().name, 'xyz')
        # # region automatically removed
        # self.assertEqual(updated.regions.count(), 0)

        # self.assertEqual(updated.sources.count(), 2)
        # source_types = list([source.stype.name for source in updated.sources.all()])
        # self.assertTrue('Vanilla' in source_types)
        # self.assertTrue('Chocolate' in source_types)

        # self.assertEqual(updated.actions_taken.count(), 0)
        # self.assertEqual(updated.contacts.count(), 1)
        # self.assertEqual(updated.visibility, models.VisibilityChoices.PUBLIC)
        # # emergency still attached
        # self.assertEqual(updated.event.id, event_pk)
        # # Translated field test
        # # (Since with with self.capture_on_commit_callbacks(execute=True) is not used so translation has not been triggered)
        # self.assertEqual(updated.summary_en, 'test [updated]')
        # self.assertEqual(updated.description_en, 'this is a test description')
        # self.assertEqual(updated.summary_es, '')  # This has been reset
        # self.assertEqual(
        #     updated.description_es,
        #     self.aws_translator._fake_translation('this is a test description', 'es', 'en'),
        # )  # This has not been reset

        # body['summary'] = 'test [updated again]'
        # with self.capture_on_commit_callbacks(execute=True):
        #     response = self.client.put(f'/api/v2/update_field_report/{created.id}/', body, format='json').json()
        # updated = models.FieldReport.objects.get(pk=response['id'])
        # self.assertEqual(updated.summary_en, 'test [updated again]')
        # self.assertEqual(
        #     updated.summary_es,
        #     self.aws_translator._fake_translation('test [updated again]', 'es', 'en'),
        # )

        # # Check with GET (with different accept-language)
        # for lang, _ in settings.LANGUAGES:
        #     response = self.client.get(f'/api/v2/field_report/{created.id}/', HTTP_ACCEPT_LANGUAGE=lang)
        #     self.assert_200(response)
        #     self.assertEqual(
        #         response.json()['summary'],
        #         self.aws_translator._fake_translation(body['summary'], lang, 'en') if lang != 'en' else body['summary'],
        #     )


class VisibilityTest(APITestCase):
    def test_country_snippet_visibility(self):
        country = models.Country.objects.create(name='1')
        # create membership and IFRC snippets
        models.CountrySnippet.objects.create(country=country, visibility=models.VisibilityChoices.MEMBERSHIP)
        models.CountrySnippet.objects.create(country=country, visibility=models.VisibilityChoices.IFRC)
        response = self.client.get('/api/v2/country_snippet/').json()
        # no snippets available to anonymous user
        self.assertEqual(response['count'], 0)

        # perform the request with an authenticated user
        user = User.objects.create(username='foo')
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/v2/country_snippet/').json()
        # one snippets available to anonymous user
        self.assertEqual(response['count'], 1)

        # perform the request with an ifrc user
        user2 = User.objects.create(username='bar')
        user2.user_permissions.add(self.ifrc_permission)
        self.client.force_authenticate(user=user2)
        response = self.client.get('/api/v2/country_snippet/').json()
        self.assertEqual(response['count'], 2)

        # perform the request with a superuser
        super_user = User.objects.create_superuser(username='baz', email='foo@baz.com', password='12345678')
        self.client.force_authenticate(user=super_user)
        response = self.client.get('/api/v2/country_snippet/').json()
        self.assertEqual(response['count'], 2)

        self.client.force_authenticate(user=None)


# class FieldReportsVisibilityTestCase(APITestCase):
#     fixtures = ['DisasterTypes',]
#     def setUp(self):
#         user = User.objects.create(username='foo')
#         User.objects.create_superuser(username='bar', email='foo@bar.com', password='12345678')
#         event = models.Event.objects.create(
#             dtype=models.DisasterType.objects.get(pk=1),
#             name='test event for FRs',
#             disaster_start_date=datetime.now()
#         )
#         models.FieldReport.objects.create(
#             dtype=models.DisasterType.objects.get(pk=1),
#             summary='membership field report',
#             bulletin='3',
#             visibility=1, # MEMBERSHIP
#             dref='2',
#             user=user,
#             event_id=event.id,
#         )
#         models.FieldReport.objects.create(
#             dtype=models.DisasterType.objects.get(pk=1),
#             summary='ifrc field report',
#             bulletin='3',
#             visibility=2, # IFRC
#             dref='2',
#             user=user,
#             event_id=event.id,
#         )
#         models.FieldReport.objects.create(
#             dtype=models.DisasterType.objects.get(pk=1),
#             summary='public field report',
#             bulletin='3',
#             visibility=3, # PUBLIC
#             dref='2',
#             user=user,
#             event_id=event.id,
#         )

#     def test_field_reports_visibility(self):
#         user = User.objects.get(username='foo')
#         user2 = User.objects.get(username='bar')

#         # perform the request without a user
#         # this user should see FRs with PUBLIC visibility
#         response = self.client.get('/api/v2/event/6').json()

#         self.assertEqual(len(response['field_reports']), 1)
#         self.assertEqual(response['field_reports'][0]['summary'], 'public field report')

#         # perform the request with an authenticated user
#         # this user should see FRs with MEMBERSHIP and PUBLIC visibility
#         self.client.force_authenticate(user=user)
#         response = self.client.get('/api/v2/event/6').json()

#         self.assertEqual(len(response['field_reports']), 2)

#         # perform the request with a superuser
#         # this user should see all FRs
#         self.client.force_authenticate(user=user2)
#         response = self.client.get('/api/v2/event/6').json()

#         self.assertEqual(len(response['field_reports']), 3)


class ActionTestCase(APITestCase):

    def test_action_api(self):
        EVENT = models.ActionType.EVENT
        EARLY_WARNING = models.ActionType.EARLY_WARNING
        NTLS = models.ActionOrg.NATIONAL_SOCIETY
        PNS = models.ActionOrg.FOREIGN_SOCIETY

        models.Action.objects.create(
            name='Test1',
            field_report_types=[EVENT, EARLY_WARNING],
            organizations=[
                NTLS,
                PNS
            ]
        )
        models.Action.objects.create(
            name='Test2',
            field_report_types=[EARLY_WARNING],
            organizations=[]
        )
        response = self.client.get('/api/v2/action/').json()
        self.assertEqual(response['count'], 2)
        res1 = response['results'][0]
        self.assertEqual(res1['name'], 'Test1')
        self.assertEqual(res1['field_report_types'], [EVENT, EARLY_WARNING])
        self.assertEqual(res1['organizations'], [NTLS, PNS])
        res2 = response['results'][1]
        self.assertEqual(res2['organizations'], [])
        self.assertEqual(res2['field_report_types'], [EARLY_WARNING])


class HistoricalEventTest(APITestCase):

    fixtures = ['DisasterTypes']

    def test_historical_events(self):
        region1 = models.Region.objects.create(name=1)
        region2 = models.Region.objects.create(name=2)
        country1 = models.Country.objects.create(name='Nepal', iso3='NPL', region=region1)
        country2 = models.Country.objects.create(name='India', iso3='IND', region=region2)
        dtype1 = models.DisasterType.objects.get(pk=1)
        dtype2 = models.DisasterType.objects.get(pk=2)
        EventFactory.create(
            name='test1',
            dtype=dtype1,
        )
        event1 = EventFactory.create(
            name='test0',
            dtype=dtype1,
            num_affected=10000,
            countries=[country1]
        )
        event2 = EventFactory.create(
            name='test2',
            dtype=dtype2,
            num_affected=99999,
            countries=[country2]
        )
        event3 = EventFactory.create(
            name='test2',
            dtype=dtype2,
            num_affected=None,
            countries=[country2]
        )
        appeal1 = AppealFactory.create(
            event=event1,
            dtype=dtype1,
            num_beneficiaries=9000,
            amount_requested=10000,
            amount_funded=1899999
        )
        appeal2 = AppealFactory.create(
            event=event2,
            dtype=dtype2,
            num_beneficiaries=90023,
            amount_requested=100440,
            amount_funded=12299999
        )
        appeal2 = AppealFactory.create(
            event=event3,
            dtype=dtype2,
            num_beneficiaries=91000,
            amount_requested=10000888,
            amount_funded=678888
        )
        response = self.client.get('/api/v2/go-historical/').json()
        self.assertEqual(response['count'], 3)  # should give event that have appeal associated with and num_affected=null
        self.assertEqual(
            sorted([event1.id, event2.id, event3.id]),
            sorted([data['id'] for data in response['results']])
        )

        # test for filter by country iso3
        response = self.client.get(f'/api/v2/go-historical/?iso3={country1.iso3}').json()
        self.assertEqual(response['count'], 1)
        self.assertEqual(response['results'][0]['id'], event1.id)
        self.assertEqual(response['results'][0]['appeals'][0]['id'], appeal1.id)

        # test for region filter by
        response = self.client.get(f'/api/v2/go-historical/?region={region1.id}').json()
        self.assertEqual(response['count'], 1)
        self.assertEqual(response['results'][0]['id'], event1.id)


class Admin2Test(APITestCase):

    def test_admin2_api(self):
        region = models.Region.objects.create(name=1)
        country = models.Country.objects.create(name='Nepal', iso3='NPL', region=region)
        admin1_1 = models.District.objects.create(name='admin1 1', code='NPL01', country=country)
        admin1_2 = models.District.objects.create(name='admin1 2', code='NPL02', country=country)
        admin2_1 = models.Admin2.objects.create(name='test 1', admin1=admin1_1, code='1')
        admin2_2 = models.Admin2.objects.create(name='test 2', admin1=admin1_2, code='2')

        # test fetching all admin2-s
        response = self.client.get('/api/v2/admin2/').json()
        self.assertEqual(response['count'], 2)

        # test filtering by district
        response = self.client.get(f'/api/v2/admin2/?admin1={admin1_1.id}').json()
        self.assertEqual(response['count'], 1)
        self.assertEqual(response['results'][0]['name'], 'test 1')

    def test_admin2_deprecation(self):
        region = models.Region.objects.create(name=1)
        country = models.Country.objects.create(name='Nepal', iso3='NPL', region=region)
        admin1_1 = models.District.objects.create(name='admin1 1', code='NPL01', country=country)
        admin1_2 = models.District.objects.create(name='admin1 2', code='NPL02', country=country)
        admin2_1 = models.Admin2.objects.create(name='test 1', admin1=admin1_1, code='1')
        admin2_2 = models.Admin2.objects.create(name='test 2', admin1=admin1_2, code='2')
        admin2_3 = models.Admin2.objects.create(name='test 3', admin1=admin1_2, code='3')

        # test fetching all admin2-s
        response = self.client.get('/api/v2/admin2/').json()
        self.assertEqual(response['count'], 3)

        admin2_2.is_deprecated = True
        admin2_2.save()
        response = self.client.get('/api/v2/admin2/').json()
        # 2 instead of 3, because 1 admin2 area became deprecated: api does not show it.
        self.assertEqual(response['count'], 2)

        # Tear down
        admin2_2.is_deprecated = False
        admin2_2.save()
        response = self.client.get('/api/v2/admin2/').json()
        self.assertEqual(response['count'], 3)

        admin2_1.is_deprecated = True
        admin2_2.is_deprecated = True
        admin2_1.save()
        admin2_2.save()
        # 2 admin2-s are deprecated, so 3-2 = 1
        response = self.client.get('/api/v2/admin2/').json()
        self.assertEqual(response['count'], 1)

        # Tear down
        admin2_1.is_deprecated = False
        admin2_2.is_deprecated = False
        admin2_1.save()
        admin2_2.save()
        response = self.client.get('/api/v2/admin2/').json()
        self.assertEqual(response['count'], 3)

        admin2_1.is_deprecated = True
        admin2_2.is_deprecated = True
        admin2_3.is_deprecated = True
        admin2_1.save()
        admin2_2.save()
        admin2_3.save()
        # All admin2-s are deprecated
        response = self.client.get('/api/v2/admin2/').json()
        self.assertEqual(response['count'], 0)

        # Tear down
        admin2_1.is_deprecated = False
        admin2_2.is_deprecated = False
        admin2_3.is_deprecated = False
        admin2_1.save()
        admin2_2.save()
        admin2_3.save()
        response = self.client.get('/api/v2/admin2/').json()
        self.assertEqual(response['count'], 3)

        admin1_2.is_deprecated = True
        admin1_2.save()
        response = self.client.get('/api/v2/admin2/').json()
        # There are 2 admin2-s in this district, so 3-2 = 1
        self.assertEqual(response['count'], 1)

        # Tear down
        admin1_2.is_deprecated = False
        admin1_2.save()
        response = self.client.get('/api/v2/admin2/').json()
        self.assertEqual(response['count'], 3)

        admin1_1.is_deprecated = True
        admin1_1.save()
        response = self.client.get('/api/v2/admin2/').json()
        # There is only 1 admin2-s in this district, so 3-1 = 2
        self.assertEqual(response['count'], 2)

        # Tear down
        admin1_1.is_deprecated = False
        admin1_1.save()
        response = self.client.get('/api/v2/admin2/').json()
        self.assertEqual(response['count'], 3)

        country.is_deprecated = True
        country.save()
        response = self.client.get('/api/v2/admin2/').json()
        # There are 3 admin2-s in this country, so 3-3 = 0
        self.assertEqual(response['count'], 0)

        # Tear down
        country.is_deprecated = False
        country.save()
        response = self.client.get('/api/v2/admin2/').json()
        self.assertEqual(response['count'], 3)


class DistrictTest(APITestCase):
    def test_district_deprecation(self):
        region = models.Region.objects.create(name=1)
        country = models.Country.objects.create(name='Nepal', iso3='NPL', region=region)
        admin1_1 = models.District.objects.create(name='admin1 1', code='NPL01', country=country)
        admin1_2 = models.District.objects.create(name='admin1 2', code='NPL02', country=country)

        # test fetching all districts
        response = self.client.get('/api/v2/district/').json()
        self.assertEqual(response['count'], 2)

        admin1_2.is_deprecated = True
        admin1_2.save()
        response = self.client.get('/api/v2/district/').json()
        # one district deprecated, 2-1 = 1
        self.assertEqual(response['count'], 1)

        # Tear down
        admin1_2.is_deprecated = False
        admin1_2.save()
        response = self.client.get('/api/v2/district/').json()
        self.assertEqual(response['count'], 2)

        admin1_1.is_deprecated = True
        admin1_2.is_deprecated = True
        admin1_1.save()
        admin1_2.save()
        response = self.client.get('/api/v2/district/').json()
        # two districts deprecated, 2-2 = 0
        self.assertEqual(response['count'], 0)

        # Tear down
        admin1_1.is_deprecated = False
        admin1_2.is_deprecated = False
        admin1_1.save()
        admin1_2.save()
        response = self.client.get('/api/v2/district/').json()
        self.assertEqual(response['count'], 2)

        country.is_deprecated = True
        country.save()
        response = self.client.get('/api/v2/district/').json()
        # There are 2 districts in this country, so 2-2 = 0
        self.assertEqual(response['count'], 0)

        # Tear down
        country.is_deprecated = False
        country.save()
        response = self.client.get('/api/v2/district/').json()
        self.assertEqual(response['count'], 2)


class GlobalEnumEndpointTest(APITestCase):
    def test_200_response(self):
        response = self.client.get('/api/v2/global-enums/')
        self.assert_200(response)
        self.assertIsNotNone(response.json())
