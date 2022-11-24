import re
import logging
import pandas as pd
import operator
from functools import reduce

from celery import shared_task
from django.db import transaction, models

from api.models import CountryType
from .models import (
    DataImport,
    CountryPlan,
    StrategicPriority,
    MembershipCoordination
)
from api.models import Country

logger = logging.getLogger(__name__)


class CountryPlanImporter():
    CSV_COLUMN = [
        'ISO3',
        'Country',
        'SP1 - Climate and environmental crisis',
        'SP2 - Evolving crises and disasters',
        'SP3 - Growing gaps in health and wellbeing',
        'SP4 - Migration and identity',
        'SP5 - Values, power, and inclusion',
        'Max of people to be reached ',
        'SP1',
        'SP2',
        'SP3',
        'SP4',
        'SP5',
        'EA1',
        'EA2',
        'EA3',
        'TOTAL\nFUNDING REQUIREMENTS',
    ]

    SP_COLUMN = [
        'SP1',
        'SP2',
        'SP3',
        'SP4',
        'SP5',
        'EA1',
        'EA2',
        'EA3',
    ]

    @staticmethod
    def _process_number(number):
        if number in ('', None):
            return None
        if type(number) in [float, int]:
            return number
        # Some sepecific case using regex
        value_search = re.search(r'(?P<value>(\d+(?:\.\d+)?))?\s?(?P<expression>(M|K|B){1})', number)
        if value_search is None or (
            value_search.group('value') is None or
            value_search.group('expression') is None
        ):
            return pd.to_numeric(number)
        value = pd.to_numeric(value_search.group('value'))
        expression = value_search.group('expression')
        EXPRESSION_MULTIPLER = {
            'K': 1000,
            'M': 1000000,
            'B': 1000000000,
        }
        return value * EXPRESSION_MULTIPLER[expression]

    @classmethod
    def _save_country_plan(cls, row):
        country = Country.objects.filter(record_type=CountryType.COUNTRY).get(iso3=row.ISO3)
        # -- Country Plan
        country_plan, _ = CountryPlan.objects.get_or_create(country=country)
        country_plan.requested_amount = cls._process_number(row._17)
        country_plan.people_targeted = cls._process_number(row._8)
        country_plan.save()

        # -- StrategicPriority
        target_values_list = [row._3, row._4, row._5, row._6, row._7]
        sp_target_value_map = dict(zip(StrategicPriority.Type, target_values_list))
        for sp, t_people in sp_target_value_map.items():
            strategic_priority, _ = StrategicPriority.objects.get_or_create(
                country_plan=country_plan,
                type=sp,
            )
            strategic_priority.people_targeted = cls._process_number(t_people)
            # strategic_priority.funding_requirement?
            strategic_priority.save()

        # -- MembershipCoordination
        n_society_list = [row.SP1, row.SP2, row.SP3, row.SP4, row.SP5, row.EA1, row.EA2, row.EA3]
        sp_column_n_society_map = dict(zip(cls.SP_COLUMN, n_society_list))
        sp_column_ns_type_map = dict(zip(cls.SP_COLUMN, MembershipCoordination.Sector))
        membership_coordination_ids = []
        for sp in cls.SP_COLUMN:
            national_societies_str = set([
                name.strip()
                for name in str(sp_column_n_society_map[sp] or '').split(',')
                if name.strip()
            ])
            if not national_societies_str:
                continue
            countries_qs = Country.objects.filter(
                reduce(
                    operator.or_, (
                        models.Q(society_name__icontains=name)
                        for name in national_societies_str
                    )
                ),
                record_type=CountryType.COUNTRY,
                in_search=True,
            )
            # TODO: Better error handling
            missing_ns_in_db = set(national_societies_str) - set(countries_qs.values_list('society_name', flat=True))
            if missing_ns_in_db:
                raise Exception(f"Missing NS in the database: {missing_ns_in_db}")
            for country in countries_qs.all():
                membership_coordination, _ = MembershipCoordination.objects.get_or_create(
                    country_plan=country_plan,
                    national_society=country,
                    sector=sp_column_ns_type_map[sp],
                )
                membership_coordination.has_coordination = True
                membership_coordination.save()
                membership_coordination_ids.append(membership_coordination.id)
        # Update dangling membership coordination
        MembershipCoordination.objects\
            .filter(country_plan=country_plan)\
            .exclude(id__in=membership_coordination_ids)\
            .update(has_coordination=False)

    @classmethod
    def process(cls, file):
        data = pd.read_excel(file, skiprows=1, na_filter=False, usecols=cls.CSV_COLUMN)
        data = data[:-1]

        errors = []
        for row in data.itertuples():
            try:
                with transaction.atomic():
                    cls._save_country_plan(row)
            except Exception as e:
                logger.error(f'Failed to import Country-Plan: iso3:{row.ISO3}', exc_info=True)
                errors.append(dict(
                    iso3=row.ISO3,
                    error=str(e),
                ))
        return errors


@shared_task
def process_data_import(pk):
    data_import = DataImport.objects.get(pk=pk)
    errors = CountryPlanImporter.process(data_import.file)
    data_import.errors = errors
    data_import.save()
