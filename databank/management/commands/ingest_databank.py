import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import Country, CronJob, CronJobStatus
from databank.models import CountryOverview

from .sources import (
    FDRS,
    FTS_HPC,
    INFORM,
    RELIEFWEB,
    START_NETWORK,
    WB,
)

logger = logging.getLogger(__name__)

SOURCES = [
    (s, s.__name__.split('.')[-1])
    for s in (
        FDRS,
        FTS_HPC,
        INFORM,
        RELIEFWEB,
        START_NETWORK,
        WB,
    )
]


class Command(BaseCommand):
    def load(self):
        """
        Load data for Databank from specified sources
        """
        source_prefetch_data = {}

        # Prefetch Data
        try:
            print('\nPrefetching from sources:: ')
            for source, name in SOURCES:
                if hasattr(source, 'prefetch'):
                    start = datetime.datetime.now()
                    print(f'\t -> {name}', end='')
                    prefetch_response = source.prefetch()
                    if prefetch_response is not None:
                        source_prefetch_data[source.__name__], item_count, sources = prefetch_response
                        # Log success prefetch
                        CronJob.sync_cron({
                            'name': name,
                            'message': f'Done querying {name}' + (
                                sources and f' using sources: {sources}'
                            ) or '',
                            'num_result': item_count,
                            'status': CronJobStatus.SUCCESSFUL,
                        })
                    print(f' [{datetime.datetime.now() - start}]')
        except Exception as ex:
            CronJob.sync_cron({
                'name': 'ingest_databank',
                'message': f'Could not prefetch from sources\n\nException:\n{str(ex)}',
                'status': CronJobStatus.ERRONEOUS,
            })

        # Load
        try:
            print('\nLoading Sources data into GO DB:: ')
            for source, name in SOURCES:
                if hasattr(source, 'global_load'):
                    print(f'\t -> {name}', end='')
                    source.global_load(source_prefetch_data.get(source.__name__))
                    print(f' [{datetime.datetime.now() - start}]')

            index, country_count = 1, Country.objects.count()
            print('\nLoading Sources data for each country to GO DB:: ')
            for country in Country.objects.prefetch_related('countryoverview').all():
                print(u'\t -> ({}/{}) {}'.format(index, country_count, str(country)))
                overview = (
                    country.countryoverview if hasattr(country, 'countryoverview') else
                    CountryOverview.objects.create(country=country)
                )
                overview.script_modified_at = timezone.now()
                for source, name in SOURCES:
                    if hasattr(source, 'load'):
                        print(f'\t\t -> {name}', end='')
                        # Load For each country
                        source_data = source_prefetch_data.get(source.__name__)
                        start = datetime.datetime.now()
                        source.load(country, overview, source_data)
                        print(f' [{datetime.datetime.now() - start}]')
                overview.save()
                index += 1
            # This source can not be checked/logged via prefetch, that is why we do it here, after the "load".
            if name == 'FTS_HPC':
                CronJob.sync_cron({
                    'name': name,
                    'message': f'Done querying {name} data feeds',
                    'num_result': index, "status": CronJobStatus.SUCCESSFUL,
                })
        except Exception as ex:
            CronJob.sync_cron({
                'name': 'ingest_databank',
                'message': f'Could not load all data\n\nException:\n{str(ex)}',
                'status': CronJobStatus.ERRONEOUS,
            })

    def handle(self, *args, **kwargs):
        start = datetime.datetime.now()
        self.load()
        print('Total time: ', datetime.datetime.now() - start)
