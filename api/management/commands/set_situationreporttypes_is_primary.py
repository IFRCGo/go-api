from django.core.management.base import BaseCommand
from api.models import SituationReportType

class Command(BaseCommand):
  help = 'Sets the default situation report types as primary. For more info read https://github.com/IFRCGo/go-frontend/issues/1008'
  def handle(self, *args, **options):
    id_list = [1, 2, 3, 5, 6, 7]
    report_types = SituationReportType.objects.filter(id__in=id_list)
    for report_type in report_types:
      report_type.is_primary = True
      report_type.save()
    print('Done')

