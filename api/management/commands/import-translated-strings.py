import os
import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Action, Country, DisasterType, SituationReportType
from api.logger import logger


class Command(BaseCommand):
    help = 'Import translated strings from a CSV. Either use the --table and --field params \
            or else the CSV has to be named like "tablename__fieldname.csv" (ex. api_country__name.csv). \
            Delimiter should be ";". Field order: original, fr, es, ar (ex. name, name_fr, name_es, name_ar)'

    missing_args_message = "Filename is missing. A shapefile with valid admin polygons is required."

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)
        parser.add_argument(
            '-t',
            '--table',
            type=str,
            help='Database table name of the translated strings'
        )
        parser.add_argument(
            '-f',
            '--field',
            type=str,
            help='Database field name of the translated strings'
        )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        ''' Example CSV header: name; name_fr; name_es; name_ar '''

        filename = kwargs['filename'][0]
        # os.path.split() [0] is the folder [1] is the filename
        tablename = kwargs['table'] or os.path.split(filename)[1].split('__')[0]
        # [:4] is to remove '.csv' from the end
        fieldname = kwargs['field'] or os.path.split(filename)[1].split('__')[1][:4]

        with open(filename, 'r') as f:
            reader = csv.reader(f, delimiter=';')
            fieldnames = next(reader)
            translations = list(reader)

            for tr in translations:
                if tablename == 'api_country':
                    # fieldname = 'name'
                    # **{fieldname: tr[0]} = name=tr[0]
                    country = Country.objects.filter(**{fieldname: tr[0]})
                    if country:
                        country.update(**{
                            fieldnames[1]: tr[1],
                            fieldnames[2]: tr[2],
                            fieldnames[3]: tr[3]
                        })
                    else:
                        logger.info(f'No Country in GO DB with the string: {tr[0]}')
                elif tablename == 'api_action':
                    action = Action.objects.filter(**{fieldname: tr[0]})
                    if action:
                        action.update(**{
                            fieldnames[1]: tr[1],
                            fieldnames[2]: tr[2],
                            fieldnames[3]: tr[3]
                        })
                    else:
                        logger.info(f'No Action in GO DB with the string: {tr[0]}')
                elif tablename == 'api_disastertype':
                    distype = DisasterType.objects.filter(**{fieldname: tr[0]})
                    if distype:
                        distype.update(**{
                            fieldnames[1]: tr[1],
                            fieldnames[2]: tr[2],
                            fieldnames[3]: tr[3]
                        })
                    else:
                        logger.info(f'No DisasterType in GO DB with the string: {tr[0]}')
                elif tablename == 'api_situationreporttype':
                    sitreptype = SituationReportType.objects.filter(**{fieldname: tr[0]})
                    if sitreptype:
                        sitreptype.update(**{
                            fieldnames[1]: tr[1],
                            fieldnames[2]: tr[2],
                            fieldnames[3]: tr[3]
                        })
                    else:
                        logger.info(f'No SituationReportType in GO DB with the string: {tr[0]}')
        print('done!')
