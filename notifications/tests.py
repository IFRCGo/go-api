from datetime import datetime, timezone
from django.conf import settings
from modeltranslation.utils import build_localized_fieldname

from notifications.management.commands.ingest_alerts import categories, timeformat
from lang.serializers import TranslatedModelSerializerMixin
from main.test_case import APITestCase

from .models import SurgeAlert, SurgeAlertType
from api.models import Region, Country, District, Admin2
from deployments.models import MolnixTag


class NotificationTestCase(APITestCase):

    def test_surge_translation(self):
        alerts = [
            [
                "FACT",  # atype
                "Information",  # category
                "Mozambique Tropical Storm DINEO",  # operation
                # message
                "Due to the very limited number of Portuguese and Spanish speakers in our roster, we would appreciate if you could please let us know your tentative availability, only in case you speak Portuguese and/or Spanish.",  # noqa: E501
                "2017-02-15",  # created_at: date
                "14:23"  # created_at: time
            ],
        ]

        surge_alerts = []
        surge_alerts_field_values = {}
        for alert in alerts:
            fields = {
                'atype': SurgeAlertType[alert[0].strip().upper()],
                'category': categories[alert[1].strip().lower()],
                'operation': alert[2].strip(),
                'message': alert[3].strip(),
                'deployment_needed': False,
                'is_private': True,
                'created_at': datetime.strptime(
                    '%s:%s' % (alert[4].strip(), alert[5].strip()), timeformat,
                ).replace(tzinfo=timezone.utc),
            }
            surge_alert = SurgeAlert(**fields)
            surge_alert.save()
            surge_alerts.append(surge_alert)
            surge_alerts_field_values[surge_alert.pk] = fields

        # Trigger translation
        with self.capture_on_commit_callbacks(execute=True):
            TranslatedModelSerializerMixin.trigger_field_translation_in_bulk(SurgeAlert, surge_alerts)

        for surge_alert in surge_alerts:
            surge_alert.refresh_from_db()
            for field in ['operation', 'message']:
                for lang, _ in settings.LANGUAGES:
                    original_value = surge_alerts_field_values[surge_alert.pk][field]
                    self.assertEqual(
                        getattr(surge_alert, build_localized_fieldname(field, lang)),
                        self.aws_translator._fake_translation(original_value, lang, 'en') if lang != 'en' else original_value,
                    )

class SurgeAlertFilteringTest(APITestCase):

    def test_filtering(self):
        region_1 = Region.objects.create(name=1)
        region_2 = Region.objects.create(name=2)
        country_1 = Country.objects.create(name='Atlantis', iso3='ATL', region=region_1)
        country_2 = Country.objects.create(name='Neptunus', iso3='NPT', region=region_2)
        molnix_tag_1 = MolnixTag.objects.create(
            molnix_id=3,
            name='OP-6700',
            description='Middle East Crisis | MENA',
            tag_type='regular',
            tag_category='molnix_operation')
        molnix_tag_2 = MolnixTag.objects.create(
            molnix_id=5,
            name='L-FRA',
            description='French',
            tag_type='language',
            tag_category='molnix_language')
        molnix_tag_3 = MolnixTag.objects.create(
            molnix_id=17,
            name='AMER',
            description='Americas Region',
            tag_type='regular',
            tag_category='molnix_region')
        surge_alert_1 = SurgeAlert.objects.create(
            message='CEA Coordinator, Floods, Atlantis', atype=6, category=2, molnix_status='active', country=country_1)
        surge_alert_1.molnix_tags.set([molnix_tag_1, molnix_tag_2])
        surge_alert_2 = SurgeAlert.objects.create(
            message='WASH Coordinator, Earthquake, Neptunus', atype=5, category=1, molnix_status='active', country=country_2)
        surge_alert_1.molnix_tags.set([molnix_tag_1, molnix_tag_2])
        surge_alert_2.molnix_tags.set([molnix_tag_1, molnix_tag_3])

        # we have 2 SurgeAlerts with 2 different Countries: A, B
        # Filtering for X, B gives 1; filtering for A, B gives both results.

        response = self.client.get('/api/v2/surge_alert/?country__iso3__in=AAA,NPT').json()
        self.assertEqual(response['count'], 1)
        self.assertEqual(response['results'][0]['molnix_tags'][0]['name'], 'OP-6700')

        response = self.client.get('/api/v2/surge_alert/?country__iso3__in=ATL,NPT').json()
        self.assertEqual(response['count'], 2)
        self.assertEqual(
            {response['results'][0]['molnix_tags'][0]['name'],
             response['results'][0]['molnix_tags'][1]['name'],
             response['results'][1]['molnix_tags'][0]['name'],
             response['results'][1]['molnix_tags'][1]['name']},
            {'OP-6700', 'L-FRA', 'AMER'})

        # we have 2 SurgeAlerts with MolnixTags A, B and A, C.
        # Filtering for A, B, C gives both. Filtering for only B or C gives 1.

        # filtering by molnix_tags
        response = self.client.get('/api/v2/surge_alert/?country__iso3__in=ATL,NPT&molnix_tags=' + str(molnix_tag_2.id)
            ).json()
        self.assertEqual(response['count'], 1)

        response = self.client.get('/api/v2/surge_alert/?country__iso3__in=ATL,NPT&molnix_tags=' \
            + str(molnix_tag_1.id) + ',' + str(molnix_tag_2.id) + ',' + str(molnix_tag_3.id)
            ).json()
        self.assertEqual(response['count'], 2)

        # filtering by molnix_tag_names
        response = self.client.get('/api/v2/surge_alert/?country__iso3__in=ATL,NPT&molnix_tag_names=' + 'AMER'
            ).json()
        self.assertEqual(response['count'], 1)

        response = self.client.get('/api/v2/surge_alert/?country__iso3__in=ATL,NPT&molnix_tag_names=' \
            + 'OP-6700,L-FRA,AMER'
            ).json()
        self.assertEqual(response['count'], 2)
