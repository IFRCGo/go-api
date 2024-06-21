import logging
import operator
import re
import typing
from functools import reduce

import pandas as pd
from celery import shared_task
from django.db import models, transaction

from api.models import Country, CountryType

from .models import CountryPlan, DataImport, MembershipCoordination, StrategicPriority

logger = logging.getLogger(__name__)


class RollBackException(Exception):
    pass


class CountryPlanImporter:
    CSV_COLUMN = [
        "ISO3",
        "Country",
        "Reach\n2024_EO",
        "Reach\n2024_SP1",
        "Reach\n2024_SP2",
        "Reach\n2024_SP3",
        "Reach\n2024_SP4",
        "Reach\n2024_SP5",
        "SP1 ",
        "SP2 ",
        "SP3 ",
        "SP4 ",
        "SP5 ",
        "EF",
        "Total FR\n2024",
    ]

    SP_COLUMN = [
        "SP1 ",
        "SP2 ",
        "SP3 ",
        "SP4 ",
        "SP5 ",
        "EF",
    ]

    @staticmethod
    def _process_number(number):
        if number in ("", None):
            return None
        if type(number) in [float, int]:
            return number
        # Some specific cases using regex
        value_search = re.search(r"(?P<value>(\d+(?:\.\d+)?))?\s?(?P<expression>[MKB])", number)
        if value_search is None or (value_search.group("value") is None or value_search.group("expression") is None):
            return pd.to_numeric(number.replace(",", ""))
        value = pd.to_numeric(value_search.group("value"))
        expression = value_search.group("expression")
        EXPRESSION_MULTIPLIER = {
            "K": 1000,
            "M": 1000000,
            "B": 1000000000,
        }
        return value * EXPRESSION_MULTIPLIER[expression]

    @classmethod
    def _save_country_plan(cls, row):
        country = Country.objects.filter(record_type=CountryType.COUNTRY).get(iso3=row.ISO3)
        # -- Country Plan
        country_plan, _ = CountryPlan.objects.get_or_create(country=country)
        people_targeted_list = [row._3, row._4, row._5, row._6, row._7, row._8]
        people_new_list = []
        for people in people_targeted_list:
            people = cls._process_number(people)
            people_new_list.append(people)
        if len(people_new_list):
            country_plan.people_targeted = max([people for people in people_new_list if people is not None], default=None)
        country_plan.requested_amount = cls._process_number(row._15)
        country_plan.save()

        # -- StrategicPriority
        target_values_list = [row._3, row._4, row._5, row._6, row._7, row._8]
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
        # NOTE: Replace whitespace in xlsx file
        n_society_list = [row._9, row._10, row._11, row._12, row._13, row.EF]
        sp_column_n_society_map = dict(zip(cls.SP_COLUMN, n_society_list))
        sp_column_ns_type_map = dict(zip(cls.SP_COLUMN, MembershipCoordination.Sector))
        membership_coordination_ids = []
        for sp in cls.SP_COLUMN:
            national_societies_str = set(
                [name.strip() for name in str(sp_column_n_society_map[sp] or "").split(",") if name.strip()]
            )
            if not national_societies_str:
                continue
            countries_qs = Country.objects.filter(
                reduce(operator.or_, (models.Q(society_name__icontains=name) for name in national_societies_str)),
                record_type=CountryType.COUNTRY,
                in_search=True,
            )
            # TODO: Better error handling
            missing_ns_in_db = set(national_societies_str) - set(countries_qs.values_list("society_name", flat=True))
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
        MembershipCoordination.objects.filter(country_plan=country_plan).exclude(id__in=membership_coordination_ids).update(
            has_coordination=False
        )

    @classmethod
    def _process(cls, data) -> typing.List[typing.Dict]:
        errors = []
        for row in data.itertuples():
            try:
                cls._save_country_plan(row)
            except Exception as e:
                logger.error(f"Failed to import Country-Plan: iso3:{row.ISO3}", exc_info=True)
                errors.append(
                    dict(
                        iso3=row.ISO3,
                        error=str(e),
                    )
                )
        return errors

    @classmethod
    def process(cls, file) -> typing.List[typing.Dict]:
        data = pd.read_excel(file, skiprows=4, na_filter=False, usecols=cls.CSV_COLUMN)
        data = data[:-1]
        errors = []

        try:
            with transaction.atomic():
                # Clean-up existing dataset StrategicPriority,MembershipCoordination
                StrategicPriority.objects.all().delete()
                MembershipCoordination.objects.all().delete()

                # Add new data
                errors = cls._process(data)
                if errors:
                    raise RollBackException()
        except Exception as e:
            # handle custom rollback error manually
            if not isinstance(e, RollBackException):
                logger.error("Failed to process Country-Plan", exc_info=True)
                errors.append(dict(error=str(e)))
            pass

        # Return errors
        return errors


@shared_task
def process_data_import(pk):
    data_import = DataImport.objects.get(pk=pk)
    errors = CountryPlanImporter.process(data_import.file)
    data_import.errors = errors
    data_import.save()
