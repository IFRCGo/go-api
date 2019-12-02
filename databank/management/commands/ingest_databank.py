import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import Country
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
        print('\nPrefetching from sources:: ')
        for source, name in SOURCES:
            if hasattr(source, 'prefetch'):
                start = datetime.datetime.now()
                print(f'\t -> {name}', end='')
                source_prefetch_data[source.__name__] = source.prefetch()
                print(f' [{datetime.datetime.now() - start}]')

        # Load
        print('\nLoading Sources data into GO DB:: ')
        for source, name in SOURCES:
            if hasattr(source, 'global_load'):
                print(f'\t -> {name}', end='')
                source.global_load(source_prefetch_data.get(source.__name__))
                print(f' [{datetime.datetime.now() - start}]')

        index, country_count = 1, Country.objects.count()
        print('\nLoading Sources data for each country to GO DB:: ')
        for country in Country.objects.prefetch_related('countryoverview').all():
            print(f'\t -> ({index}/{country_count}) {country}')
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

    def handle(self, *args, **kwargs):
        start = datetime.datetime.now()
        self.load()
        print('Total time: ', datetime.datetime.now() - start)
