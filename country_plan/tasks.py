import logging
import pandas as pd
from celery import shared_task
import re
from django.db.models import Q
import operator
from functools import reduce

from .models import (
    DataImport,
    CountryPlan,
    StrategicPriority,
    MembershipCoordination
)
from api.models import Country

logger = logging.getLogger(__name__)


@shared_task
def process_data_import(pk):
    csv_column = [
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

    data_import = DataImport.objects.get(pk=pk)
    data = pd.read_excel(data_import.file, skiprows=1, na_filter=False, usecols=csv_column)
    data = data[:-1]

    for dl in data.itertuples():
        print(dl)
        iso3 = dl.ISO3
        country = Country.objects.get(iso3=iso3)
        country_plan, created = CountryPlan.objects.get_or_create(
            country=country
        )
        requested_amount = dl._17
        if isinstance(requested_amount, str):
            requested_amount = re.findall(r'\d+(?:\.\d+)?', requested_amount)
            country_plan.requested_amount = float(requested_amount[0]) * 1000000 if not requested_amount == [] else 0
        else:
            requested_amount = requested_amount
            country_plan.requested_amount = requested_amount

        country_plan.people_targeted = dl._8 if not dl._8 == '' else None
        country_plan.save()

        target_values_list = [dl._3, dl._4, dl._5, dl._6, dl._7]
        sp_target_value_map = dict(zip(StrategicPriority.Type, target_values_list))
        for sp, t_people in sp_target_value_map.items():
            strategic_priority, created = StrategicPriority.objects.get_or_create(
                country_plan=country_plan,
                sp_name=sp
            )
            strategic_priority.people_targeted = t_people if not t_people == '' else None
            strategic_priority.save()
        n_society_list = [dl.SP1, dl.SP2, dl.SP3, dl.SP4, dl.SP5, dl.EA1, dl.EA2, dl.EA3]
        sp_column = ['SP1', 'SP2', 'SP3', 'SP4', 'SP5', 'EA1', 'EA2', 'EA3']
        sp_column_n_society_map = dict(zip(sp_column, n_society_list))
        sp_column_ns_type_map = dict(zip(sp_column, MembershipCoordination.Type))
        for sp in sp_column:
            ns = sp_column_n_society_map[sp] if not sp_column_n_society_map[sp] == '' else None
            if ns:
                ns_list = str(ns).split(',')
                filters = reduce(operator.or_, (Q(society_name__icontains=item.strip()) for item in ns_list))
                country_list = Country.objects.filter(filters)
                for country in country_list:
                    membership_coordination, created = MembershipCoordination.objects.get_or_create(
                        country_plan=country_plan,
                        national_society=country,
                        strategic_priority=sp_column_ns_type_map[sp]
                    )

