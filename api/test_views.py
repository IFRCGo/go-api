from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission
from django.conf import settings

from main.test_case import APITestCase
import api.models as models


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
        print(response)
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
        body = {
            'countries': [country1.id, country2.id],
            'dtype': 7,
            'summary': 'test',
            'description': 'this is a test description',
            'bulletin': '3',
            'num_assisted': 100,
            'visibility': models.VisibilityChoices.IFRC,
            'sources': [
                {'stype': 'Government', 'spec': 'A source'},
                {'stype': 'Other', 'spec': 'Another source'},
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
        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post('/api/v2/create_field_report/', body, format='json').json()
        created = models.FieldReport.objects.get(pk=response['id'])

        self.assertEqual(created.countries.count(), 2)
        # one region attached automatically
        self.assertEqual(created.regions.count(), 1)

        self.assertEqual(created.sources.count(), 2)
        source_types = list([source.stype.name for source in created.sources.all()])
        self.assertTrue('Government' in source_types)
        self.assertTrue('Other' in source_types)

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
        self.assertEqual(
            created.summary_es,
            self.aws_translator._fake_translation('test', 'es', 'en')
        )

        # created an emergency automatically
        self.assertEqual(created.event.name, 'test')
        event_pk = created.event.id

        body['countries'] = [country2.id]
        body['summary'] = 'test [updated]'
        body['sources'] = [
            {'stype': 'Vanilla', 'spec': 'something'},
            {'stype': 'Chocolate', 'spec': 'other'},
        ]
        body['actions_taken'] = []
        body['visibility'] = models.VisibilityChoices.PUBLIC
        response = self.client.put(f'/api/v2/update_field_report/{created.id}/', body, format='json').json()
        updated = models.FieldReport.objects.get(pk=response['id'])

        self.assertEqual(updated.countries.count(), 1)
        self.assertEqual(updated.countries.first().name, 'xyz')
        # region automatically removed
        self.assertEqual(updated.regions.count(), 0)

        self.assertEqual(updated.sources.count(), 2)
        source_types = list([source.stype.name for source in updated.sources.all()])
        self.assertTrue('Vanilla' in source_types)
        self.assertTrue('Chocolate' in source_types)

        self.assertEqual(updated.actions_taken.count(), 0)
        self.assertEqual(updated.contacts.count(), 1)
        self.assertEqual(updated.visibility, models.VisibilityChoices.PUBLIC)
        # emergency still attached
        self.assertEqual(updated.event.id, event_pk)
        # Translated field test
        # (Since with with self.capture_on_commit_callbacks(execute=True) is not used so translation has not been triggered)
        self.assertEqual(updated.summary_en, 'test [updated]')
        self.assertEqual(updated.description_en, 'this is a test description')
        self.assertEqual(updated.summary_es, None)  # This has been reset
        self.assertEqual(
            updated.description_es,
            self.aws_translator._fake_translation('this is a test description', 'es', 'en'),
        )  # This has not been reset

        body['summary'] = 'test [updated again]'
        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.put(f'/api/v2/update_field_report/{created.id}/', body, format='json').json()
        updated = models.FieldReport.objects.get(pk=response['id'])
        self.assertEqual(updated.summary_en, 'test [updated again]')
        self.assertEqual(
            updated.summary_es,
            self.aws_translator._fake_translation('test [updated again]', 'es', 'en'),
        )

        # Check with GET (with different accept-language)
        for lang, _ in settings.LANGUAGES:
            response = self.client.get(f'/api/v2/field_report/{created.id}/', HTTP_ACCEPT_LANGUAGE=lang)
            self.assert_200(response)
            self.assertEqual(
                response.json()['summary'],
                self.aws_translator._fake_translation(body['summary'], lang, 'en') if lang != 'en' else body['summary'],
            )


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
        ifrc_permission = Permission.objects.create(
            codename='ifrc_admin',
            name='IFRC Admin',
            content_type=ContentType.objects.get_for_model(models.Country),
        )
        user2.user_permissions.add(ifrc_permission)
        self.client.force_authenticate(user=user2)
        response = self.client.get('/api/v2/country_snippet/').json()
        self.assertEqual(response['count'], 2)

        # perform the request with a superuser
        super_user = User.objects.create_superuser(username='baz', email='foo@baz.com', password='12345678')
        self.client.force_authenticate(user=super_user)
        response = self.client.get('/api/v2/country_snippet/').json()
        self.assertEqual(response['count'], 2)

        self.client.force_authenticate(user=None)


class FieldReportsVisibilityTestCase(APITestCase):
    fixtures = ['DisasterTypes',]
    def setUp(self):
        user = User.objects.create(username='foo')
        User.objects.create_superuser(username='bar', email='foo@bar.com', password='12345678')
        event = models.Event.objects.create(
            dtype=models.DisasterType.objects.get(pk=1),
            name='test event for FRs',
            disaster_start_date=datetime.now()
        )
        models.FieldReport.objects.create(
            dtype=models.DisasterType.objects.get(pk=1),
            summary='membership field report',
            bulletin='3',
            visibility=1, # MEMBERSHIP
            dref='2',
            user=user,
            event_id=event.id,
        )
        models.FieldReport.objects.create(
            dtype=models.DisasterType.objects.get(pk=1),
            summary='ifrc field report',
            bulletin='3',
            visibility=2, # IFRC
            dref='2',
            user=user,
            event_id=event.id,
        )
        models.FieldReport.objects.create(
            dtype=models.DisasterType.objects.get(pk=1),
            summary='public field report',
            bulletin='3',
            visibility=3, # PUBLIC
            dref='2',
            user=user,
            event_id=event.id,
        )
    
    def test_field_reports_visibility(self):
        user = User.objects.get(username='foo')
        user2 = User.objects.get(username='bar')

        # perform the request without a user
        # this user should see FRs with PUBLIC visibility
        response = self.client.get('/api/v2/event/6')
        response = json.loads(response.content)

        self.assertEqual(len(response['field_reports']), 1)
        self.assertEqual(response['field_reports'][0]['summary'], 'public field report')

        # perform the request with an authenticated user
        # this user should see FRs with MEMBERSHIP and PUBLIC visibility
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/v2/event/6')
        response = json.loads(response.content)

        self.assertEqual(len(response['field_reports']), 2)

        # perform the request with a superuser
        # this user should see all FRs
        self.client.force_authenticate(user=user2)
        response = self.client.get('/api/v2/event/6')
        response = json.loads(response.content)

        self.assertEqual(len(response['field_reports']), 3)


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
