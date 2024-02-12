import logging
import json
import requests
from django.core.management.base import BaseCommand
from api.models import Country, CountryType
from collections import defaultdict
from databank.models import CountryKeyClimate, CountryOverview
from datetime import datetime

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Add minimum, maximum and Average temperature of country temperature data from source api'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start_date',
            action='store',
            help='Start date to fetch temperature data in the format YYYY-MM-DD'
        )
        parser.add_argument(
            '--end_date',
            action='store',
            help='End date to fetch temperature data in the format YYYY-MM-DD'
        )

    def handle(self, *args, **options):
        for co in CountryOverview.objects.filter(country__record_type=CountryType.COUNTRY).all():
            centroid = getattr(co.country, 'centroid', None)
            if centroid:
                centroid = json.loads(centroid.geojson)

                lat = centroid.get("coordinates", [])[1]
                lon = centroid.get("coordinates", [])[0]
                if options['start_date'] and options['end_date']:
                    response = requests.get(f'https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={options["start_date"]}&end_date={options["end_date"]}&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,precipitation_hours')
                else:
                    response = requests.get(f'https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=2023-01-01&end_date=2023-12-31&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,precipitation_hours')
                if response.status_code != 200:
                    continue
                response.raise_for_status()
                try:
                    data = response.json()
                    daily_data = data.get('daily', {})
                    if daily_data:
                        monthly_temperatures = defaultdict(list)

                        for i, date_str in enumerate(daily_data.get('time', [])):
                            max_temp = daily_data.get('temperature_2m_max')[i]
                            min_temp = daily_data.get('temperature_2m_min')[i]
                            precipitation = daily_data.get('precipitation_sum')[i]
                            if date_str and max_temp is not None and min_temp is not None:
                                date = datetime.strptime(date_str, '%Y-%m-%d')
                                month_key = (date.year, date.month)
                                monthly_temperatures[month_key].append((max_temp, min_temp, precipitation))
                        # Calculate min, max, and avg temperatures for each month
                        for month_key, temps in monthly_temperatures.items():
                            year, month = month_key
                            max_temp_monthly = max(temps, key=lambda x: x[0])[0]
                            min_temp_monthly = min(temps, key=lambda x: x[1])[1]
                            avg_temp_monthly = (max_temp_monthly + min_temp_monthly) / 2
                            precipitation_monthly = sum([x[2] for x in temps])

                            CountryKeyClimate.objects.create(
                                overview=co,
                                year=year,
                                month=month,
                                max_temp=max_temp_monthly,
                                min_temp=min_temp_monthly,
                                avg_temp=avg_temp_monthly,
                                precipitation=precipitation_monthly
                            )
                        logger.info('Minimum, maximum and Average temperature of country temperature data added successfully')
                        print('Minimum, maximum and Average temperature of country temperature data added successfully')

                except Exception as ex:
                    logger.error(f'Error in ingesting climate data: {ex}')
                    print(f'Error in ingesting climate data: {ex}')
                    continue
