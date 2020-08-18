from datetime import datetime, timezone
from django.conf import settings
from modeltranslation.utils import build_localized_fieldname

from notifications.management.commands.ingest_alerts import categories, timeformat
from lang.serializers import TranslatedModelSerializerMixin
from main.test_case import APITestCase

from .models import SurgeAlert, SurgeAlertType


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
