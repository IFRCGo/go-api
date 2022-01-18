import requests
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from notifications.models import SurgeAlertType, SurgeAlertCategory, SurgeAlert
from lang.serializers import TranslatedModelSerializerMixin


categories = {
    'information': SurgeAlertCategory.INFO,
    'deployment': SurgeAlertCategory.DEPLOYMENT,
    'alert': SurgeAlertCategory.ALERT,
    'shelter deployment': SurgeAlertCategory.SHELTER,
    'stand down': SurgeAlertCategory.STAND_DOWN,
}


timeformat = '%Y-%m-%d:%H:%M'


class Command(BaseCommand):
    help = 'Ingest alerts data'

    def id_from_model(self, model):
        timestring = datetime.strftime(model.created_at, timeformat)
        return '%s:%s' % (timestring, model.atype)

    def id_from_alert(self, alert):
        atype = SurgeAlertType[alert[0].strip().upper()]
        return '%s:%s:%s' % (alert[4], alert[5], atype)

    def handle(self, *args, **options):
        url = (
            'https://proxy.hxlstandard.org/data.json?'
            'url=https%3A//docs.google.com/spreadsheets/d/1eVpS1Bob4G2KzSwco6ELTzIsYHKvqKsNQI7ZdAzmPuQ&strip-headers=on'
        )

        response = requests.get(url)
        if response.status_code != 200:
            raise Exception('Error querying Appeals API')
        alerts = response.json()

        aids = [self.id_from_model(m) for m in SurgeAlert.objects.all()]
        print('%s current surge alerts' % len(aids))

        # The first alert is headers
        new_alerts = [a for a in alerts[1:] if self.id_from_alert(a) not in aids]
        print('%s alerts ingesting' % len(new_alerts))

        surge_alerts = []
        for alert in new_alerts:
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

        # Trigger translation
        TranslatedModelSerializerMixin.trigger_field_translation_in_bulk(SurgeAlert, surge_alerts)
        print('%s current surge alerts' % SurgeAlert.objects.all().count())
