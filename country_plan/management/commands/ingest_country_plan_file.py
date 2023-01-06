import logging
import requests
from typing import Union
from datetime import datetime
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import models

from api.models import CronJob, CronJobStatus
from country_plan.models import CountryPlan

logger = logging.getLogger(__name__)

NAME = 'ingest_country_plan_file'
# Ref: https://github.com/IFRCGo/go-api/issues/1614
SOURCE = 'https://go-api.ifrc.org/api/publicsiteappeals?AppealsTypeID=1851&Hidden=false'


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

    def load_for_country(self, country_data):
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
        country_plan = CountryPlan.objects.filter(
            models.Q(country__iso__iexact=country_iso2) |
            models.Q(country__name__iexact=country_name)
        ).first()
        if country_plan is None:
            logger.warning(f'{NAME} No country_plan found for: {(country_iso2, country_name)}')
            return
        if country_plan.appeal_api_inserted_date and country_plan.appeal_api_inserted_date >= inserted_date:
            # No need to do anything here
            return
        public_plan_url = country_data['BaseDirectory'] + country_data['BaseFileName']
        country_plan.appeal_api_inserted_date = inserted_date
        country_plan.load_file_to_country_plan(
            public_plan_url,
            # NOTE: File provided are PDF,
            f"public-plan-{country_data['BaseFileName']}.pdf",
        )
        country_plan.is_publish = True
        country_plan.save(
            update_fields=(
                'appeal_api_inserted_date',
                'public_plan_file',  # By load_file_to_country_plan
                'is_publish',
            )
        )
        return True

    def load(self):
        updated = 0
        auth = (settings.APPEALS_USER, settings.APPEALS_PASS)
        results = requests.get(SOURCE, auth=auth, headers={'Accept': 'application/json'}).json()
        for result in results:
            try:
                if self.load_for_country(result):
                    updated += 1
            except Exception as ex:
                logger.error('Could not Updated countries plan', exc_info=True)
                country_info = (
                    result.get('LocationCountryCode'),
                    result.get('LocationCountryName'),
                )
                CronJob.sync_cron({
                    'name': NAME,
                    'message': f"Could not updated country plan for {country_info}\n\nException:\n{str(ex)}",
                    'status': CronJobStatus.ERRONEOUS,
                })
        return updated

    def handle(self, *args, **kwargs):
        try:
            logger.info('\nFetching data for country plans:: ')
            countries_plan_updated = self.load()
            CronJob.sync_cron({
                'name': NAME,
                'message': 'Updated countries plan',
                'num_result': countries_plan_updated,
                'status': CronJobStatus.SUCCESSFUL,
            })
            logger.info('Updated countries plan')
        except Exception as ex:
            logger.error('Could not Updated countries plan', exc_info=True)
            CronJob.sync_cron({
                'name': NAME,
                'message': f'Could not Updated countries plan\n\nException:\n{str(ex)}',
                'status': CronJobStatus.ERRONEOUS,
            })
