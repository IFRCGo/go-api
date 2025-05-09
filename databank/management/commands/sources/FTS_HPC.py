import csv
import datetime
import io

import requests

from .utils import catch_error, get_country_by_iso2

# from django.conf import settings
# from api.utils import base64_encode


FTS_URL = "https://api.hpc.tools/v1/public/fts/flow?countryISO3={0}&groupby=year&report=3"
EMERGENCY_URL = "https://api.hpc.tools/v1/public/emergency/country/{0}"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1MArQSVdbLXLaQ8ixUKo9jIjifTCVDDxTJYbGoRuw3Vw/gviz/tq?tqx=out:csv"

HEADERS = {
    # TODO: USE Crendentils here
    # 'Authorization': 'Basic {}'.format(base64_encode(settings.HPC_CREDENTIAL))
}


@catch_error()
def prefetch():
    g_sheet_data = requests.get(GOOGLE_SHEET_URL, headers=HEADERS)
    g_sheet_data.raise_for_status()

    g_sheet_data = list(csv.DictReader(io.StringIO(g_sheet_data.text)))

    gho_data = {}
    for d in g_sheet_data:
        if (
            "Country #country+code" in d
            and "Year #date+year" in d
            and "PIN #inneed" in d
            and "PT #targeted" in d
            and "Funding #value+required+total+usd" in d
            and "Requirements #value+funding+required+usd" in d
        ):
            key = f"{d['Country #country+code'].upper()}-{d['Year #date+year']}"
            gho_data[key] = {
                "people_in_need": d["PIN #inneed"],
                "people_targeted": d["PT #targeted"],
                "funding_total_usd": d["Funding #value+required+total+usd"],
                "funding_required_usd": d["Requirements #value+funding+required+usd"],
            }
        else:
            print(f"Warning: Skipping FTS_HPC data due to missing keys: {d}")

    return gho_data, len(gho_data), GOOGLE_SHEET_URL


@catch_error()
def load(country, overview, gho_data):
    if country.iso is None or gho_data is None:
        return
    pcountry = get_country_by_iso2(country.iso)
    if pcountry is None:
        return
    fts_data = requests.get(FTS_URL.format(pcountry.alpha_3), headers=HEADERS)
    emg_data = requests.get(EMERGENCY_URL.format(pcountry.alpha_3), headers=HEADERS)

    fts_data.raise_for_status()
    emg_data.raise_for_status()

    fts_data = fts_data.json()
    emg_data = emg_data.json()

    c_data = {}

    # fundingTotals, pledgeTotals
    for fund_area, fund_area_s in [("fundingTotals", "funding_totals"), ("pledgeTotals", "pledge_totals")]:
        fund_area_data = fts_data["data"]["report3"][fund_area]["objects"]
        if len(fund_area_data) > 0:
            for v in fund_area_data[0]["objectsBreakdown"]:
                try:
                    year = int(v["name"])
                    totalFunding = v["totalFunding"]
                except ValueError:
                    continue
                if year not in c_data:
                    c_data[year] = {fund_area_s: totalFunding}
                else:
                    c_data[year][fund_area_s] = totalFunding

    # numActivations
    CronJobSum = 0
    for v in emg_data["data"]:
        try:
            year = datetime.datetime.strptime(
                v["date"].split("T")[0],
                "%Y-%m-%d",
            ).year
        except ValueError:
            continue
        if year not in c_data:
            c_data[year] = {"numActivations": 1}
        else:
            c_data[year]["numActivations"] = c_data[year].get("numActivations", 0) + 1
        CronJobSum += c_data[year]["numActivations"]

    overview.fts_data = [
        {
            "year": year,
            **values,
            **gho_data.get(f"{pcountry.alpha_3.upper()}-{year}", {}),
        }
        for year, values in c_data.items()
    ]
    overview.save()

    # Instead of here the CronJob success logging was placed to ingest_databank.py, because here it is in a loop
