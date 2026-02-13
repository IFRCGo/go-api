import json
import time
from datetime import date, datetime, timedelta

import pandas as pd
import pycountry
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand


def iso3_to_country_name(iso3_code: str) -> str:
    try:
        country = pycountry.countries.get(alpha_3=iso3_code)
        return country.name if country else ""
    except LookupError:
        return ""


def get_inform_workflow_candidates():
    base_url = "https://drmkc.jrc.ec.europa.eu/Inform-Index/API/InformAPI/workflows/GetByWorkflowGroup"
    years_to_try = [date.today().year, date.today().year - 1]
    workflow_candidates = []

    for year in years_to_try:
        response = requests.get(f"{base_url}/INFORM{year}")
        workflows = response.json() or []
        if not workflows:
            continue

        name_priority = [
            f"INFORM Risk {year} with UCDP",
            f"INFORM Risk {year}",
            f"INFORM Risk Mid {year}",
        ]

        for name in name_priority:
            matches = [wf for wf in workflows if wf.get("Name") == name]
            for match in matches:
                workflow_candidates.append((match.get("WorkflowId"), year, name))

    if not workflow_candidates:
        raise RuntimeError("No INFORM workflows found for the current or previous year.")

    return workflow_candidates


def fetch_inform_indicators(workflow_id: int, year: int) -> pd.DataFrame:
    i = "INFORM,CC,HA,VU,HA.NAT,HA.NAT-EPI,HA.NAT.DR,HA.NAT.TC,HA.NAT.FL,HA.NAT.CFL,HA.NAT.EQ,HA.NAT.TS,HA.HUM"
    response = requests.get(
        "https://drmkc.jrc.ec.europa.eu/Inform-Index/API/InformAPI/countries/Scores/",
        params={
            "WorkflowId": workflow_id,
            "IndicatorId": i,
        },
    )
    response.raise_for_status()
    payload = response.json()
    if not payload:
        raise RuntimeError("INFORM API returned no data for the selected workflow.")

    df_indicator = pd.DataFrame(payload)
    if "IndicatorId" in df_indicator.columns:
        df_indicator.rename(columns={"IndicatorId": "Indicator"}, inplace=True)

    if "IndicatorScore" in df_indicator.columns:
        df_indicator.rename(columns={"IndicatorScore": "Value"}, inplace=True)
    elif "IndicatorValue" in df_indicator.columns:
        df_indicator.rename(columns={"IndicatorValue": "Value"}, inplace=True)
    elif "Value" not in df_indicator.columns:
        raise KeyError(f"INFORM API response missing score column. Available columns: {list(df_indicator.columns)}")

    iso3_candidates = ["Iso3", "ISO3", "iso3", "Iso3Code"]
    iso3_column = next((c for c in iso3_candidates if c in df_indicator.columns), None)
    if not iso3_column:
        raise KeyError(f"INFORM API response missing ISO3 column. Available columns: {list(df_indicator.columns)}")

    df_indicator.rename(columns={iso3_column: "Iso3"}, inplace=True)
    df_indicator["Year"] = year

    df_inform_risk = df_indicator.pivot_table(index="Iso3", columns="Indicator", values="Value", fill_value=0)
    df_inform_risk = df_inform_risk.reset_index()
    df_inform_risk.rename(
        columns={
            "CC": "Lack of coping capacity",
            "HA": "Hazard & exposure",
            "INFORM": "INFORM RISK",
            "VU": "Vulnerability",
            "HA.HUM": "Human",
            "HA.NAT": "Natural",
            "HA.NAT-EPI": "Epidemic",
            "HA.NAT.DR": "Drought",
            "HA.NAT.EQ": "Earthquake",
            "HA.NAT.FL": "River Flood",
            "HA.NAT.CFL": "Coastal Flood",
            "HA.NAT.TC": "Tropical Cyclone",
            "HA.NAT.TS": "Tsunami",
        },
        inplace=True,
    )
    return df_inform_risk


def pcv_mapping(indicator: float) -> float:
    return indicator * 0.3


def remove_square_brackets(df: pd.DataFrame) -> pd.DataFrame:
    def remove_brackets_from_list(lst):
        if isinstance(lst, list) and len(lst) > 0:
            return str(lst[0]).replace("[", "").replace("]", "")
        return lst

    for col in ["country", "drivers", "iso3", "regions"]:
        if col in df.columns:
            df[col] = df[col].apply(remove_brackets_from_list)
            df[col] = df[col].fillna("").astype(str)
    return df


def fetch_acaps_paginated(url: str, token: str) -> pd.DataFrame:
    df = pd.DataFrame()
    last_request_time = datetime.now()
    request_url = url
    while True:
        while (datetime.now() - last_request_time).total_seconds() < 1:
            time.sleep(0.1)
        response = requests.get(request_url, headers={"Authorization": f"Token {token}"})
        response.raise_for_status()
        payload = response.json()
        df = pd.concat([df, pd.DataFrame(payload.get("results"))])
        if payload.get("next"):
            request_url = payload["next"]
        else:
            break
    return df


def ifrc_security_phase(value: str):
    if value in [None, ""]:
        return None
    mapping = {"Orange": 2, "Red": 3, "White": 1, "Yellow": 1}
    return mapping.get(value)


def bin_severity_index(severity_index):
    if severity_index is None:
        return None
    if severity_index < 2:
        return 1
    if 2 <= severity_index < 4:
        return 2
    return 3


def bin_impact_index_database(impact_index):
    if impact_index < 2:
        return 1
    if 2 <= impact_index < 4:
        return 2
    return 3


def bin_impact_index_user_input(impact_index):
    if impact_index < 2:
        return 1
    if 2 <= impact_index < 3:
        return 2
    return 3


def bin_affected(affected_population):
    if affected_population is None:
        return None
    if affected_population < 500000:
        return 1
    if 500000 <= affected_population < 2000000:
        return 2
    return 3


def bin_percentage_affected(percentage):
    if percentage is None:
        return None
    if percentage < 0.10:
        return 1
    if 0.10 <= percentage < 0.20:
        return 2
    if 0.20 <= percentage < 10:
        return 3
    return None


def bin_casualties(casualties):
    if casualties is None:
        return None
    casualties = int(casualties)
    if casualties < 100:
        return 1
    if 100 <= casualties <= 999:
        return 2
    return 3


def bin_pin(pin):
    if pin is None:
        return None
    pin = int(pin)
    if pin < 100000:
        return 1
    if 100000 <= pin < 500000:
        return 2
    return 3


def fetch_worldometer_population():
    url = "https://www.worldometers.info/world-population/population-by-country/"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", {"class": "datatable w-full border border-zinc-200"})
    countries = []
    populations = []
    if table:
        rows = table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all("td")
            countries.append(cols[1].text.strip())
            populations.append(cols[2].text.strip())
    df_pop = pd.DataFrame({"Country": countries, "Population": populations})
    df_pop["Iso3"] = df_pop["Country"].apply(
        lambda x: pycountry.countries.get(name=x).alpha_3 if pycountry.countries.get(name=x) else ""
    )
    df_pop["Population"] = df_pop["Population"].astype(str).str.replace(",", "").astype(float)
    return df_pop


def count_emergencies_last_36_months():
    temp_dict = requests.get("https://goadmin.ifrc.org/api/v2/appeal").json()
    dict_field = []
    while temp_dict.get("next"):
        dict_field.extend(temp_dict["results"])
        temp_dict = requests.get(temp_dict["next"]).json()
    dict_field.extend(temp_dict.get("results", []))
    df = pd.DataFrame.from_dict(dict_field)
    if df.empty:
        return pd.DataFrame(columns=["Iso3", "emergency_count"])
    df["country_iso3"] = [x["iso3"] for x in df["country"]]
    df["start_date"] = pd.to_datetime(df["start_date"], utc=True, errors="coerce")
    current_date = datetime.now(tz=pd.Timestamp.utcnow().tz)
    three_years_ago = current_date - timedelta(days=36 * 30)
    filtered_df = df[df["start_date"] >= three_years_ago]
    country_emergency_count = filtered_df.groupby("country_iso3").size().reset_index(name="emergency_count")
    all_iso_df = pd.DataFrame({"country_iso3": df["country_iso3"].unique()})
    final_df = pd.merge(all_iso_df, country_emergency_count, on="country_iso3", how="left")
    final_df["emergency_count"] = final_df["emergency_count"].fillna(0).astype(int)
    final_df.rename(columns={"country_iso3": "Iso3"}, inplace=True)
    return final_df


def bin_number_staffs(nb_staff):
    if nb_staff is None:
        return None
    if nb_staff < 50:
        return 3
    if 50 <= nb_staff < 500:
        return 2
    return 1


def bin_ratio(ratio):
    if ratio is None:
        return None
    if ratio <= 0.008:
        return 3
    if 0.008 < ratio <= 0.12:
        return 2
    return 1


def bin_dref_ea(nb):
    if nb is None:
        return None
    if nb <= 2:
        return 3
    if 2 < nb <= 4:
        return 2
    return 1


class Command(BaseCommand):
    help = "Run ACC calculations (no GUI) with API-based inputs only"

    def add_arguments(self, parser):
        parser.add_argument("--iso3", required=True, help="ISO3 code of the country (e.g. AFG)")
        parser.add_argument(
            "--event-type",
            required=False,
            help="Event type (Natural, Epidemic, Drought, Earthquake, River Flood, Coastal Flood, Tropical Cyclone, Tsunami, "
            + "Human). If omitted, all are evaluated.",
        )
        parser.add_argument("--acaps-token", required=False, help="ACAPS API token")
        parser.add_argument("--acaps-access-date", default="Mar2025", help="ACAPS humanitarian access date (e.g. Mar2025)")
        parser.add_argument("--acaps-impact-date", default="Mar2025", help="ACAPS inform severity impact date (e.g. Mar2025)")
        parser.add_argument("--acaps-severity-date", default="", help="ACAPS inform severity date (blank for latest)")
        parser.add_argument("--crisis-name-access", default="", help="ACAPS crisis name for access selection")
        parser.add_argument("--crisis-name-impact", default="", help="ACAPS crisis name for impact selection")
        parser.add_argument("--crisis-name-severity", default="", help="ACAPS crisis name for severity selection")
        parser.add_argument("--government-response", type=float, default=None, help="Government response score (1-3)")
        parser.add_argument("--media-attention", type=float, default=None, help="Media attention score (1-3)")
        parser.add_argument("--ifrc-security-phase", default=None, help="IFRC security phase (White/Yellow/Orange/Red)")
        parser.add_argument("--people-affected", type=float, default=None, help="Number of people affected")
        parser.add_argument("--people-in-need", type=float, default=None, help="People in need")
        parser.add_argument("--casualties", type=float, default=None, help="Casualties (wounded/dead/missing)")
        parser.add_argument(
            "--impact-score", type=float, default=None, help="Manual impact score (1-3) if not using ACAPS impact"
        )
        parser.add_argument(
            "--severity-score", type=float, default=None, help="Manual severity score (1-3) if not using ACAPS severity"
        )
        parser.add_argument("--population", type=float, default=None, help="Population of affected area (optional)")
        parser.add_argument("--fdrs-api-key", default=None, help="FDRS API key (optional, for capacity indicators)")

    def handle(self, *args, **options):
        iso3 = options["iso3"].upper()
        event_type_map = {
            "Natural": "Natural",
            "Epidemic": "Epidemic",
            "Drought": "Drought",
            "Earthquake": "Earthquake",
            "River Flood": "River Flood",
            "Coastal Flood": "Coastal Flood",
            "Tropical Cyclone": "Tropical Cyclone",
            "Tsunami": "Tsunami",
            "Human": "Human",
            "Conflict": "Human",
            "Human conflict": "Human",
        }
        valid_event_types = [
            "Natural",
            "Epidemic",
            "Drought",
            "Earthquake",
            "River Flood",
            "Coastal Flood",
            "Tropical Cyclone",
            "Tsunami",
            "Human",
        ]
        event_type_input = (options.get("event_type") or "").strip()
        if event_type_input:
            event_type = event_type_map.get(event_type_input, event_type_input)
            event_type_list = [event_type]
        else:
            event_type_list = valid_event_types

        df_inform = None
        last_error = None
        workflow_year = None
        for workflow_id, year, workflow_name in get_inform_workflow_candidates():
            try:
                df_inform = fetch_inform_indicators(workflow_id, year)
                workflow_year = year
                break
            except RuntimeError as exc:
                last_error = f"{workflow_name} ({year}): {exc}"

        if df_inform is None:
            raise RuntimeError("INFORM API returned no data for the tried workflows. Last error: " + (last_error or "unknown"))

        if event_type_input:
            for event_type in event_type_list:
                if event_type not in df_inform.columns:
                    missing = event_type_input or event_type
                    raise ValueError(f"Unknown event type '{missing}'. Valid values: {', '.join(valid_event_types)}.")
        else:
            event_type_list = [etype for etype in event_type_list if etype in df_inform.columns]
            if not event_type_list:
                raise ValueError("None of the default event types are available in the INFORM dataset for this workflow.")

        iso3_row = df_inform[df_inform["Iso3"] == iso3]
        if iso3_row.empty:
            raise ValueError(f"ISO3 '{iso3}' not found in INFORM data for workflow {workflow_year}.")

        vulnerability = float(iso3_row["Vulnerability"].iloc[0])
        coping = float(iso3_row["Lack of coping capacity"].iloc[0])

        # Complexity
        access_value = None
        if options.get("acaps-token"):
            access_url = f"https://api.acaps.org/api/v1/humanitarian-access/{options['acaps-access-date']}/"
            df_access = fetch_acaps_paginated(access_url, options["acaps-token"])
            df_access = remove_square_brackets(df_access)
            df_access.rename(columns={"iso3": "Iso3"}, inplace=True)
            df_access = df_access[df_access["Iso3"] == iso3]
            crisis_name = options.get("crisis-name-access") or (df_access["crisis_name"].iloc[0] if not df_access.empty else "")
            if crisis_name:
                match = df_access[df_access["crisis_name"] == crisis_name]
                if not match.empty:
                    access_value = match["ACCESS"].iloc[0]

        complexity_inputs = [
            (access_value * 0.6) if access_value is not None else None,
            options.get("government-response"),
            options.get("media-attention"),
            ifrc_security_phase(options.get("ifrc-security-phase")),
        ]
        complexity_series = pd.Series([v for v in complexity_inputs if v is not None])
        complexity_indicator = complexity_series.mean() if not complexity_series.empty else None

        # Scope & Scale
        impact_index_value = None
        if options.get("acaps-token"):
            impact_url = f"https://api.acaps.org/api/v1/inform-severity-index/{options['acaps-impact-date']}/"
            df_impact = fetch_acaps_paginated(impact_url, options["acaps-token"])
            df_impact = remove_square_brackets(df_impact)
            df_impact.rename(columns={"iso3": "Iso3"}, inplace=True)
            df_impact = df_impact[df_impact["Iso3"] == iso3]
            crisis_name = options.get("crisis-name-impact") or (df_impact["crisis_name"].iloc[0] if not df_impact.empty else "")
            if crisis_name:
                match = df_impact[df_impact["crisis_name"] == crisis_name]
                if not match.empty:
                    impact_index_value = bin_impact_index_database(match["Impact of the crisis"].iloc[0])

        if impact_index_value is None and options.get("impact-score") is not None:
            impact_index_value = bin_impact_index_user_input(options["impact-score"])

        population = options.get("population")
        if population is None:
            df_pop = fetch_worldometer_population()
            population_match = df_pop[df_pop["Iso3"] == iso3]
            if not population_match.empty:
                population = population_match["Population"].iloc[0]

        people_affected = options.get("people-affected")
        percentage_affected = (people_affected / population) if people_affected and population else None

        scope_scores = pd.Series(
            [
                bin_affected(people_affected),
                bin_percentage_affected(percentage_affected),
                bin_severity_index(impact_index_value),
            ]
        )
        scope_indicator = scope_scores.dropna().mean() if not scope_scores.dropna().empty else None

        # Humanitarian conditions
        severity_value = None
        if options.get("acaps-token"):
            severity_url = "https://api.acaps.org/api/v1/inform-severity-index/"
            if options.get("acaps-severity-date"):
                severity_url = f"https://api.acaps.org/api/v1/inform-severity-index/{options['acaps-severity-date']}/"
            df_severity = fetch_acaps_paginated(severity_url, options["acaps-token"])
            df_severity = remove_square_brackets(df_severity)
            df_severity.rename(columns={"iso3": "Iso3"}, inplace=True)
            df_severity = df_severity[df_severity["Iso3"] == iso3]
            crisis_name = options.get("crisis-name-severity") or (
                df_severity["crisis_name"].iloc[0] if not df_severity.empty else ""
            )
            if crisis_name:
                match = df_severity[df_severity["crisis_name"] == crisis_name]
                if not match.empty:
                    severity_value = match["INFORM Severity Index"].iloc[0]

        if severity_value is None and options.get("severity-score") is not None:
            severity_value = options["severity-score"]

        conditions_scores = pd.Series(
            [
                bin_severity_index(severity_value),
                bin_pin(options.get("people-in-need")),
                bin_casualties(options.get("casualties")),
            ]
        )
        humanitarian_conditions_indicator = conditions_scores.dropna().mean() if not conditions_scores.dropna().empty else None

        # Capacity & Response (no local xlsx)
        capacity_indicator = None
        df_go = count_emergencies_last_36_months()
        dref_ea = None
        if not df_go.empty:
            match = df_go[df_go["Iso3"] == iso3]
            if not match.empty:
                dref_ea = match["emergency_count"].iloc[0]

        number_of_staffs = None
        number_of_volunteers = None
        ratio_staffs_to_volunteers = None
        if options.get("fdrs-api-key"):
            api_key = options["fdrs-api-key"]
            kpi_codes = ["KPI_PeopleVol_Tot", "KPI_PStaff_Tot"]
            year = str(date.today().year)
            results = []
            for kpi_code in kpi_codes:
                resp = requests.get(
                    "https://data-api.ifrc.org/api/KpiValue",
                    params={"kpicode": kpi_code, "year": year, "apiKey": api_key},
                )
                if resp.ok:
                    results.extend(resp.json())
            df_fdrs = pd.json_normalize(data=results) if results else pd.DataFrame()
            if not df_fdrs.empty:
                df_fdrs = df_fdrs[df_fdrs["iso3"] == iso3]
                number_of_staffs = df_fdrs[df_fdrs["kpicode"] == "KPI_PStaff_Tot"]["value"].astype(float).mean()
                number_of_volunteers = df_fdrs[df_fdrs["kpicode"] == "KPI_PeopleVol_Tot"]["value"].astype(float).mean()
                if number_of_staffs and number_of_volunteers:
                    ratio_staffs_to_volunteers = number_of_staffs / number_of_volunteers

        capacity_scores = pd.Series(
            [
                bin_dref_ea(dref_ea),
                bin_number_staffs(number_of_staffs),
                bin_ratio(ratio_staffs_to_volunteers),
            ]
        )
        capacity_indicator = capacity_scores.dropna().mean() if not capacity_scores.dropna().empty else None

        outputs = []
        for event_type in event_type_list:
            event_value = float(iso3_row[event_type].iloc[0])
            pcv_scaled = pd.Series(
                {
                    "event": pcv_mapping(event_value),
                    "vulnerability": pcv_mapping(vulnerability),
                    "coping": pcv_mapping(coping),
                }
            )
            pcv_indicator = pcv_scaled.mean()

            final_scores = pd.Series(
                [
                    pcv_indicator,
                    complexity_indicator,
                    humanitarian_conditions_indicator,
                    scope_indicator,
                    capacity_indicator,
                ]
            )
            final_cc = final_scores.dropna().mean() if not final_scores.dropna().empty else None

            outputs.append(
                {
                    "iso3": iso3,
                    "event_type": event_type,
                    "pre_crisis_vulnerability": pcv_indicator,
                    "complexity": complexity_indicator,
                    "humanitarian_conditions": humanitarian_conditions_indicator,
                    "scope_and_scale": scope_indicator,
                    "capacity_and_response": capacity_indicator,
                    "cc_final": final_cc,
                }
            )

        self.stdout.write(json.dumps(outputs if len(outputs) > 1 else outputs[0], indent=2))
