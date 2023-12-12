import typing
from datetime import datetime, timezone
from django.conf import settings
from modeltranslation.utils import build_localized_fieldname

from notifications.management.commands.ingest_alerts import categories, timeformat
from lang.serializers import TranslatedModelSerializerMixin
from main.test_case import APITestCase

from api.factories.region import RegionFactory
from api.factories.country import CountryFactory
from deployments.factories.molninx_tag import MolnixTagFactory

from notifications.models import SurgeAlert, SurgeAlertType
from notifications.factories import SurgeAlertFactory


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
        region_1, region_2 = RegionFactory.create_batch(2)
        country_1 = CountryFactory.create(iso3='ATL', region=region_1)
        country_2 = CountryFactory.create(iso3='NPT', region=region_2)

        molnix_tag_1 = MolnixTagFactory.create(name='OP-6700')
        molnix_tag_2 = MolnixTagFactory.create(name='L-FRA')
        molnix_tag_3 = MolnixTagFactory.create(name='AMER')

        SurgeAlertFactory.create(
            message='CEA Coordinator, Floods, Atlantis',
            country=country_1,
            molnix_tags=[molnix_tag_1, molnix_tag_2],
        )
        SurgeAlertFactory.create(
            message='WASH Coordinator, Earthquake, Neptunus',
            country=country_2,
            molnix_tags=[molnix_tag_1, molnix_tag_3],
        )

        # we have 2 SurgeAlerts with 2 different Countries: A, B
        # Filtering for X, B gives 1; filtering for A, B gives both results.

        def _fetch(filters):
            return self.client.get('/api/v2/surge_alert/', filters).json()

        def _to_csv(*items):
            return ','.join([str(i) for i in items])

        response = _fetch(dict(country__iso3__in='AAA,NPT'))
        self.assertEqual(response['count'], 1)
        self.assertEqual(response['results'][0]['molnix_tags'][0]['name'], 'OP-6700')

        response = _fetch(dict(country__iso3__in='ATL,NPT'))
        self.assertEqual(response['count'], 2)
        self.assertEqual(
            {
                response['results'][0]['molnix_tags'][0]['name'],
                response['results'][0]['molnix_tags'][1]['name'],
                response['results'][1]['molnix_tags'][0]['name'],
                response['results'][1]['molnix_tags'][1]['name']
            },
            {'OP-6700', 'L-FRA', 'AMER'})

        # we have 2 SurgeAlerts with MolnixTags A, B and A, C.
        # Filtering for A, B, C gives both. Filtering for only B or C gives 1.

        # filtering by molnix_tags

        response = _fetch(dict(
            country__iso3__in='ATL,NPT',
            molnix_tags=_to_csv(molnix_tag_2.id),
        ))
        self.assertEqual(response['count'], 1)

        response = _fetch(dict(
            country__iso3__in='ATL,NPT',
            molnix_tags=_to_csv(molnix_tag_1.id, molnix_tag_2.id, molnix_tag_3.id),
        ))
        self.assertEqual(response['count'], 2)

        response = _fetch(dict(
            country__iso3__in='ATL,NPT',
            molnix_tag_names=_to_csv('AMER'),
        ))
        self.assertEqual(response['count'], 1)

        response = _fetch(dict(
            country__iso3__in='ATL,NPT',
            molnix_tag_names=_to_csv('OP-6700', 'L-FRA', 'AMER'),
        ))
        self.assertEqual(response['count'], 2)
