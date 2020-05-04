from django.core.management.base import BaseCommand
from api.models import FieldReport

class Command(BaseCommand):
    help = 'Copies all EPI Field Report figures from health_min, who, other fields into the epi fields'
    def handle(self, *args, **options):
        print('%s EPI Field Reports' % FieldReport.objects.filter(dtype=1).count())

        epi_field_reports = list(FieldReport.objects.filter(dtype=1).prefetch_related())
        for fr in epi_field_reports:
            fr.epi_cases = fr.health_min_cases or fr.who_cases or fr.other_cases
            fr.epi_suspected_cases = fr.health_min_suspected_cases or fr.who_suspected_cases or fr.other_suspected_cases
            fr.epi_probable_cases = fr.health_min_probable_cases or fr.who_probable_cases or fr.other_probable_cases
            fr.epi_confirmed_cases = fr.health_min_confirmed_cases or fr.who_confirmed_cases or fr.other_confirmed_cases
            fr.epi_num_dead = fr.health_min_num_dead or fr.who_num_dead or fr.other_num_dead
            fr.save()
        print ('Done!')
