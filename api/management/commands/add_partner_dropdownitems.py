from django.core.management.base import BaseCommand, CommandError
from api.models import ExternalPartner, SupportedActivity
from django.db import transaction
from django.db.models import Q
from api.logger import logger

class Command(BaseCommand):
    help = 'Adds predefined tooltip texts to Actions (most probably one-time run only)'

    @transaction.atomic
    def handle(self, *args, **options):
        partners = [
            'MOH', 'WHO', 'UNICEF', 'WFP', 'Other UN agencies', 'Civil Society and NGO partners'
        ]
        activities = [
            'COVID-19 testing',
            'Point of entry/ point of control screening',
            'Contact tracing',
            'Support for people in quarantine',
            'Support for mild/ moderate cases in isolation',
            'Risk communication and community engagement',
            'Health and hygiene promotion',
            'Surveillance, including active case finding',
            'Community-based surveillance',
            'Infection prevention and control (including WASH) in health facilities',
            'Community WASH activities to reduce the risk of COVID-19 transmission',
            'MHPSS support related to COVID-19',
            'Isolation and clinical case management of COVID-19 cases',
            'Support for COVID-19 vaccination',
            'Ambulance services for COVID-19 cases',
            'Maintaining non-COVID-19 ambulatory services',
            'Blood services',
            'Maintaining access to essential health services (e.g. routine immunization, malaria, elder care)',
            'Management of the dead',
            'Livelihoods activities',
            'Food and in-kind assistance',
            'Cash and voucher assistance',
            'Skills development for livelihoods / economic activities',
            'Shelter',
            'Provision of safe and adequate shelter and settlements',
            'Other',
        ]

        error = False
        p_to_add = []
        a_to_add = []
        partners_empty = not ExternalPartner.objects.exists()
        activities_empty = not SupportedActivity.objects.exists()

        if partners_empty:
            for par in partners:
                extpar = ExternalPartner(
                    name=par,
                    name_en=par
                )
                p_to_add.append(extpar)

            try:
                ExternalPartner.objects.bulk_create(p_to_add)
            except Exception as ex:
                logger.error(f'Could not create ExternalPartners. Error: {str(ex)}')
                error = True
        if activities_empty:
            for act in activities:
                supact = SupportedActivity(
                    name=act,
                    name_en=act
                )
                a_to_add.append(supact)

            try:
                SupportedActivity.objects.bulk_create(a_to_add)
            except Exception as ex:
                logger.error(f'Could not create SupportedActivities. Error: {str(ex)}')
                error = True

        if not error:
            logger.info('Successfully added ExternalPartners and SupportedActivities.')