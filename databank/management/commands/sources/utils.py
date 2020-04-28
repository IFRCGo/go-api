import pycountry
import logging
import traceback

from api.models import Country
from api.models import CronJob, CronJobStatus
from django.db import transaction

logger = logging.getLogger(__name__)


# Custom error catch (for catching errors only)
# Make sure country is provided in first argument only
def catch_error(error_message=None):
    def _dec(func):
        def _caller(*args, **kwargs):
            source_name = func.__module__.split('.')[-1]
            country = args[0] if (
                len(args) > 0 and isinstance(args[0], Country)
            ) else None
            try:
                with transaction.atomic():
                    return func(*args, **kwargs)
            except Exception as e:
                # Log error to cronjob
                CronJob.sync_cron({
                    'name': source_name,
                    'message': (
                        f'Error querying {source_name}.' +
                        (f' For Country: {country}.' if country else '') +
                        f'\n\n' + traceback.format_exc()
                    ),
                    'status': CronJobStatus.ERRONEOUS,
                })
                logger.error(
                    f"Failed to load <{source_name}:{func.__name__}>" + (
                        f'For Country: {country}' if country else ''
                    ) + (
                        f' {error_message}' if error_message else ''
                    ),
                    exc_info=True,
                )
        _caller.__name__ = func.__name__
        _caller.__module__ = func.__module__
        return _caller
    return _dec


PYCOUNTRY_MISSED_COUNTRY = {
    'cape verde': 'CPV',
    'syria': 'SYR',
    'gaza strip': 'GAZ',
    'north korea': 'PRK',
    'netherlands antilles': 'ANT',
    # 'south korea': 'KOR',
}


def get_country_by_name(name):
    country = pycountry.countries.get(name=name)
    if country:
        return country
    try:
        return pycountry.countries.lookup(name)
    except LookupError:
        return pycountry.countries.get(
            alpha_3=PYCOUNTRY_MISSED_COUNTRY[name.lower()]
        )


def get_country_by_iso2(iso2):
    return pycountry.countries.get(alpha_2=iso2.upper())


def get_country_by_iso3(iso3):
    return pycountry.countries.get(alpha_3=iso3.upper())
