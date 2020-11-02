import csv
from django.db import transaction
from django.core.management.base import BaseCommand
from per.models import FormArea, FormComponent, FormQuestion


class Command(BaseCommand):
    help = 'Imports old PER translations from CSV'
    missing_args_message = "filename, type or areanum are missing"

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)
        parser.add_argument(
            '-t',
            '--type',
            nargs='+',
            type=str,
            help='Type must be one of the following: areas, components, questions'
        )
        parser.add_argument(
            '-a',
            '--areanum',
            type=str,
            help='Area number must be an integer'
        )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        filename = kwargs['filename'][0]
        objtype = kwargs['type'][0]
        area_num = kwargs['areanum'][0]

        with open(filename, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            fieldnames = next(reader)
            rows = list(reader)

            if objtype == 'areas':
                for row in rows:
                    FormArea.objects.create(**{
                        fieldnames[0]: row[0],
                        fieldnames[1]: row[1],
                        fieldnames[2]: row[2],
                        fieldnames[3]: row[3],
                        fieldnames[4]: row[4],
                        fieldnames[5]: row[5]
                    })
            elif objtype == 'components':
                for row in rows:
                    area = FormArea.objects.filter(area_num=area_num).first()
                    if area:
                        FormComponent.objects.create(**{
                            'area_id': area.id,
                            fieldnames[0]: row[0],
                            fieldnames[1]: row[1],
                            fieldnames[2]: row[2],
                            fieldnames[3]: row[3],
                            fieldnames[4]: row[4],
                            fieldnames[5]: row[5],
                            fieldnames[6]: row[6],
                            fieldnames[7]: row[7],
                            fieldnames[8]: row[8],
                            fieldnames[9]: row[9],
                            fieldnames[10]: row[10],
                            fieldnames[11]: row[11]
                        })
            elif objtype == 'questions':
                for row in rows:
                    if not row[0] and not row[1]:
                        continue
                    comp_num = row[0]
                    comp = FormComponent.objects.filter(component_num=comp_num).first()
                    if comp:
                        FormQuestion.objects.create(**{
                            'component_id': comp.id,
                            fieldnames[1]: row[1],
                            fieldnames[2]: row[2],
                            fieldnames[3]: row[3],
                            fieldnames[4]: row[4],
                            fieldnames[5]: row[5],
                            fieldnames[6]: row[6]
                        })
        print('done!')


        # import_file = open(options['import_missing'], 'r')
        # import_missing = import_file.read().splitlines()
        # centroid_file = csv.DictReader(open(options['update_centroid'], 'r'), fieldnames=['country', 'latitude', 'longitude', 'name'])
        # for row in centroid_file:
        #     code = row['country'].lower()
        #     lat = row['latitude']
        #     lon = row['longitude']
        #     if (lat != '' and lon != ''):
        #         country_centroids[code] = Point(float(lon), float(lat))



        # print('%s current events' % Event.objects.all().count())

        # appeals_without_events = list(Appeal.objects.filter(event__isnull=True))
        # print ('Creating %s events' % len(appeals_without_events))
        # for appeal in appeals_without_events:
        #     fields = {
        #         'name': appeal.name,
        #         'dtype': appeal.dtype,
        #         'disaster_start_date': appeal.start_date,
        #         'auto_generated': True,
        #         'auto_generated_source': SOURCES['appeal_admin'],
        #     }
        #     event = Event.objects.create(**fields)
        #     if appeal.country is not None:
        #         event.countries.add(appeal.country)
        #     if appeal.region is not None:
        #         event.regions.add(appeal.region)
        #     appeal.event = event
        #     appeal.save()

        # print('%s current events' % Event.objects.all().count())
