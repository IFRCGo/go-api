import logging
import requests
from typing import Union
from datetime import datetime
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand
from django.core.files.base import File
from django.conf import settings
from django.db import models

from main.utils import DownloadFileManager
from api.models import Country
from country_plan.models import CountryPlan

logger = logging.getLogger(__name__)

# Ref: https://github.com/IFRCGo/go-api/issues/1614
PUBLIC_SOURCE = 'https://go-api.ifrc.org/api/publicsiteappeals?AppealsTypeID=1851&Hidden=false'
# Ref: https://github.com/IFRCGo/go-api/issues/1648
INTERNAL_SOURCE = 'https://go-api.ifrc.org/Api/FedNetAppeals?AppealsTypeId=1844&Hidden=false'


class Command(BaseCommand):
    @staticmethod
    def parse_date(text: str) -> Union[datetime, None]:
        """
        Convert Appeal API datetime into django datetime
        Parameters
        ----------
          text : str
              Datetime eg: 2022-11-29T11:24:00
        """
        if text:
            return make_aware(
                # NOTE: Format is assumed by looking at the data from Appeal API
                datetime.strptime(text, '%Y-%m-%dT%H:%M:%S')
            )

    @staticmethod
    def load_file_to_country_plan(country_plan: CountryPlan, url: str, filename: str, field_name: str):
        with DownloadFileManager(url, suffix='.pdf') as f:
            getattr(country_plan, field_name).save(
                filename,
                File(f),
            )

    def load_for_country(self, country_data, file_field, field_inserted_date_field):
        country_iso2 = country_data.get('LocationCountryCode')
        country_name = country_data.get('LocationCountryName')
        public_plan_url = country_data.get('BaseDirectory') or '' + country_data.get('BaseFileName') or ''
        inserted_date = self.parse_date(country_data.get('Inserted'))
        if (
            (country_iso2 is None and country_name is None) or
            public_plan_url is None or
            inserted_date is None
        ):
            return
        country_qs = Country.objects.filter(
            models.Q(iso__iexact=country_iso2) |
            models.Q(name__iexact=country_name)
        )
        country_plan = CountryPlan.objects.filter(country__in=country_qs).first()
        if country_plan is None:
            country = country_qs.first()
            # If there is no country as well, show warning and return
            if not country:
                logger.warning(f'{file_field} No country found for: {(country_iso2, country_name)}')
                return
            # Else create one and continue
            country_plan = CountryPlan(country=country)
        existing_inserted_date = getattr(country_plan, field_inserted_date_field, None)
        if existing_inserted_date and existing_inserted_date >= inserted_date:
            # No need to do anything here
            return
        self.stdout.write(f'- Saving data for country:: {country_plan.country.name}')
        public_plan_url = country_data['BaseDirectory'] + country_data['BaseFileName']
        setattr(country_plan, field_inserted_date_field, inserted_date)
        self.load_file_to_country_plan(
            country_plan,
            public_plan_url,
            # NOTE: File provided are PDF,
            f"{file_field.replace('_', '-').replace('file', '')}-{country_data['BaseFileName']}.pdf",
            file_field,
        )
        country_plan.is_publish = True
        country_plan.save(
            update_fields=(
                field_inserted_date_field,
                file_field,  # By load_file_to_country_plan
                'is_publish',
            )
        )
        return True

    def load(self, url: str, file_field: str, field_inserted_date_field: str):
        auth = (settings.APPEALS_USER, settings.APPEALS_PASS)
        results = requests.get(url, auth=auth, headers={'Accept': 'application/json'}).json()
        for result in results:
            try:
                self.load_for_country(result, file_field, field_inserted_date_field)
            except Exception:
                logger.error('Could not Updated countries plan', exc_info=True)

    def handle(self, **_):
        # Public
        self.stdout.write('Fetching data for country plans:: PUBLIC')
        self.load(PUBLIC_SOURCE, 'public_plan_file', 'public_plan_inserted_date')
        # Private
        self.stdout.write('\nFetching data for country plans:: PRIVATE')
        self.load(INTERNAL_SOURCE, 'internal_plan_file', 'internal_plan_inserted_date')
