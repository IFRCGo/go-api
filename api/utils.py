import base64
import typing
from typing import Optional, TypedDict

from django.core.exceptions import ValidationError
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext

if typing.TYPE_CHECKING:
    from api.models import Country, DisasterType, Event


class DebugPlaywright:
    """Basic helpers to debug PlayWright issues locally"""

    @staticmethod
    def log_console(msg):
        """Console logs"""
        print("console:", msg.text)

    @staticmethod
    def log_request(request):
        """Network request logs"""
        # Add filter to remove noise: if request.url.startswith("http://api/v2"):
        print("Network >>:", request.method, request.url)
        print(" --- ", request.headers)

    @staticmethod
    def log_response(response):
        """Network response logs"""
        # Add filter to remove noise: if response.url.startswith("http://api/v2"):
        print("Network <<:", response.status, response.url)
        print(" --- ", response.headers)

    @classmethod
    def debug(cls, page):
        """Add hook to receive logs from playwright"""
        page.on("console", cls.log_console)
        page.on("request", cls.log_request)
        page.on("response", cls.log_response)


def pretty_request(request):
    headers = ""
    for header, value in request.META.items():
        if not header.startswith("HTTP"):
            continue
        header = "-".join([h.capitalize() for h in header[5:].lower().split("_")])
        headers += "{}: {}\n".format(header, value)

    return (
        "{method} HTTP/1.1\n" "Content-Length: {content_length}\n" "Content-Type: {content_type}\n" "{headers}\n\n" "{body}"
    ).format(
        method=request.method,
        content_length=request.META["CONTENT_LENGTH"],
        content_type=request.META["CONTENT_TYPE"],
        headers=headers,
        body=request.body,
    )


def base64_encode(string):
    return base64.urlsafe_b64encode(string.encode("UTF-8")).decode("ascii")


def validate_slug_number(value):
    if value[0].isdigit():
        raise ValidationError(gettext("slug should not start with a number"))


def is_user_ifrc(user):
    """Checks if the user has IFRC Admin or superuser permissions"""
    if user.has_perm("api.ifrc_admin") or user.is_superuser:
        return True
    return False


# Hardwired search phrase -> pre-defined URL mapping.
# TODO: move to a model/DB table if this needs to be editable without a deploy.
SEARCH_PREDEFINED_LINKS = [
    (
        {"surge deployments", "active deployments", "deployed staff", "deployed personnel", "rapid response deployment"},
        "/surge/active-surge-deployments",
        "Active Surge Deployments",
    ),
    (
        {"surge", "surge dashboard", "rapid response", "eru"},
        "/surge/overview",
        "Surge Overview",
    ),
    (
        {"rapid response personnel", "surge staff", "surge roster", "deployable personnel"},
        "/surge/overview/rapid-response-personnel",
        "Rapid Response Personnel",
    ),
    (
        {"eru", "emergency response unit", "eru deployment", "eru capacity"},
        "/surge/overview/emergency-response-unit",
        "Emergency Response Unit",
    ),
    (
        {"surge alerts", "open surge positions", "deployment vacancies", "rapid response alerts"},
        "/alerts/all",
        "Surge Alerts",
    ),
    (
        {"deployed personnel", "all deployments", "rapid response deployments"},
        "/deployed-personnels/all",
        "All Deployed Personnel",
    ),
    (
        {
            "operational toolbox",
            "operations toolbox",
            "response toolbox",
            "emergency guidance",
            "templates by sector",
            "operational guidance",
            "surge toolbox",
        },
        "/surge/operational-toolbox",
        "Operational Toolbox",
    ),
    (
        {"surge catalogue", "catalogue of surge services", "surge roles", "role profiles", "erus", "technical competencies"},
        "/surge/catalogue/overview",
        "Catalogue of Surge Services",
    ),
    (
        {"administration", "admin support"},
        "/surge/catalogue/administration",
        "Administration",
    ),
    (
        {"cva", "cash assistance", "cash transfer programming", "vouchers"},
        "/surge/catalogue/cash",
        "Cash and Vouchers Assistance (CVA)",
    ),
    (
        {"cmr", "civil military relations"},
        "/surge/catalogue/other/civil-military-relations",
        "Civil Military Relations (CMR)",
    ),
    (
        {"communications", "media", "public information"},
        "/surge/catalogue/communication",
        "Communications",
    ),
    (
        {"cea", "community engagement", "accountability to affected people", "aap"},
        "/surge/catalogue/community-engagement",
        "Community Engagement and Accountability (CEA)",
    ),
    (
        {"digital surge", "it support", "humanitarian technology", "ict"},
        "/surge/catalogue/digital-systems",
        "Digital Systems, Tools & Information Technology",
    ),
    (
        {"drr", "disaster risk reduction", "resilience"},
        "/surge/catalogue/other/disaster-risk-reduction",
        "Disaster Risk Reduction (DRR)",
    ),
    (
        {"drones", "uav", "aerial imagery", "drone mapping"},
        "/surge/catalogue/other/uav",
        "Drones – Uncrewed Aerial Vehicles (UAV)",
    ),
    (
        {"needs assessment", "rapid assessment", "initial assessment"},
        "/surge/catalogue/emergency-needs-assessment",
        "Emergency Needs Assessment",
    ),
    (
        {"green response", "environmental sustainability"},
        "/surge/catalogue/other/green-response",
        "Green Response (GR)",
    ),
    (
        {"health surge", "emergency health", "public health"},
        "/surge/catalogue/health",
        "Health",
    ),
    (
        {"humanitarian diplomacy", "hd", "advocacy"},
        "/surge/catalogue/other/humanitarian-diplomacy",
        "Humanitarian Diplomacy (HD)",
    ),
    (
        {"human resources", "hr surge", "people management"},
        "/surge/catalogue/other/human-resources",
        "Human Resources (HR)",
    ),
    (
        {"information management", "im", "data analysis", "mapping", "gis", "geospatial", "dashboards"},
        "/surge/catalogue/information-management",
        "Information Management (IM)",
    ),
    (
        {"idrl", "disaster law", "legal preparedness"},
        "/surge/catalogue/other/international-disaster-response-law",
        "International Disaster Response Law (IDRL)",
    ),
    (
        {"livelihoods", "basic needs", "lbn", "food security"},
        "/surge/catalogue/livelihood",
        "Livelihoods and Basic Needs (LBN)",
    ),
    (
        {"logistics", "supply chain", "procurement", "fleet", "warehousing"},
        "/surge/catalogue/logistics",
        "Logistics",
    ),
    (
        {"migration", "displacement", "migrants"},
        "/surge/catalogue/other/migration",
        "Migration",
    ),
    (
        {"nsd", "national society development", "branch development"},
        "/surge/catalogue/other/national-society-development",
        "National Society Development (NSD)",
    ),
    (
        {"operations management", "operations manager", "field coordinator"},
        "/surge/catalogue/operations-management",
        "Operations Management",
    ),
    (
        {"operations support hub", "osh", "basecamp"},
        "/surge/catalogue/basecamp",
        "Operations Support HUB (OSH)",
    ),
    (
        {"pmer", "monitoring and evaluation", "reporting", "m&e"},
        "/surge/catalogue/pmer",
        "Planning, Monitoring, Evaluation and Reporting (PMER)",
    ),
    (
        {"per", "preparedness assessment", "response capacity"},
        "/surge/catalogue/other/preparedness-effective-response",
        "Preparedness for Effective Response (PER)",
    ),
    (
        {"pgi", "protection gender inclusion", "safeguarding", "disability inclusion"},
        "/surge/catalogue/pgi",
        "Protection, Gender and Inclusion (PGI)",
    ),
    (
        {"recovery", "early recovery", "recovery planning"},
        "/surge/catalogue/other/recovery",
        "Recovery",
    ),
    (
        {"relief", "relief distribution", "nfi", "household items"},
        "/surge/catalogue/relief",
        "Relief",
    ),
    (
        {"risk management", "operational risk"},
        "/surge/catalogue/risk-management",
        "Risk Management",
    ),
    (
        {"security", "field security", "safety and security"},
        "/surge/catalogue/security",
        "Security",
    ),
    (
        {"shelter", "emergency shelter", "settlements"},
        "/surge/catalogue/shelter",
        "Shelter",
    ),
    (
        {"sprm", "resource mobilisation", "donor relations", "fundraising", "funding coverage"},
        "/surge/catalogue/other/strategic-partnership-resource-mobilisation",
        "Strategic Partnerships and Resource Mobilisation (SPRM)",
    ),
    (
        {"wash", "water sanitation hygiene", "hygiene promotion"},
        "/surge/catalogue/wash",
        "Water, Sanitation, and Hygiene (WASH)",
    ),
    (
        {"risk watch", "seasonal risk", "forecast", "climate risk", "hazard monitoring"},
        "/risk-watch/seasonal",
        "Risk Watch - Seasonal",
    ),
    (
        {"preparedness resources", "preparedness tools", "ns preparedness"},
        "/preparedness/resources-catalogue",
        "Preparedness Resources Catalogue",
    ),
    (
        {"per global summary", "preparedness overview", "preparedness assessment results"},
        "/preparedness/global-summary",
        "PER Global Summary",
    ),
    (
        {"per performance", "preparedness performance", "response capacity"},
        "/preparedness/global-performance",
        "PER Global Performance",
    ),
    (
        {"emergencies", "active emergencies", "disasters", "current crises"},
        "/emergencies/all",
        "Emergencies",
    ),
    (
        {"operations", "appeals", "emergency appeals", "dref operations", "response funding"},
        "/appeals/all",
        "Operations and Appeals",
    ),
    (
        {"operational learning", "learn", "lessons learned", "after action review", "aar", "evaluations"},
        "/operational-learning",
        "Operational Learning",
    ),
    (
        {"survey designer", "questionnaire builder", "form designer", "survey builder", "xlsform", "data collection form"},
        "https://surveydesigner.ifrc.org/",
        "Survey Designer",
    ),
    (
        {"wiki", "go wiki", "go documentation", "user guide", "help", "how to use go", "go guidance"},
        "https://go-wiki.ifrc.org/en/home",
        "GO Wiki",
    ),
    (
        {"go blog", "go news", "go updates", "product updates", "new go features"},
        "https://ifrcgoproject.medium.com/",
        "GO Blog",
    ),
    (
        {
            "montandon",
            "monty",
            "global crisis data bank",
            "disaster database",
            "hazard data",
            "impact data",
            "stac",
            "historical disasters",
            "montandon api",
        },
        "/montandon-landing",
        "Montandon - Global Crisis Data Bank",
    ),
    (
        {"montandon data", "global crisis databank", "methodology", "partners", "disaster data platform"},
        "https://montandondata.org/",
        "Montandon public website",
    ),
    (
        {"montandon notebooks", "cookbook", "disaster analytics", "stac notebooks", "python disaster data", "jupyter"},
        "https://ifrcgo.org/montandon-notebooks/",
        "Montandon Data Cookbook and Notebooks",
    ),
    (
        {"register go", "create go account", "sign up", "access go"},
        "/register",
        "IFRC GO registration",
    ),
    (
        {"go source code", "github", "open source", "go repository", "developer resources"},
        "https://github.com/ifrcgo",
        "IFRC GO Open Source Code",
    ),
    (
        {"go api", "api documentation", "developer api", "data api", "integration", "endpoints"},
        "https://go-api.ifrc.org/docs/",
        "GO API Documentation",
    ),
    (
        {"kobo", "kobotoolbox", "mobile data collection", "field data collection", "surveys"},
        "https://kobo.ifrc.org/",
        "IFRC KoboToolbox",
    ),
    (
        {"kobo faq", "kobo help", "kobo guidance", "data collection help"},
        "https://www.ifrc.org/ifrc-kobo",
        "IFRC KoboToolbox FAQ",
    ),
]


def get_predefined_search_urls(phrase: str) -> list[dict]:
    """Returns all pre-defined {url, name} entries matching a known search phrase (a phrase may map to more than one)"""
    if not phrase:
        return []
    normalized_phrase = phrase.strip().lower()
    return [{"url": url, "name": name} for expressions, url, name in SEARCH_PREDEFINED_LINKS if normalized_phrase in expressions]


COUNTRY_SEARCH_CACHE_KEY = "search:country-name-to-id-map:v1"
COUNTRY_SEARCH_CACHE_TIMEOUT_SECONDS = 60 * 60  # 1 hour

# Per-country search phrase suffix/prefix -> URL template ({id} is substituted with the matched country's id).
COUNTRY_CATEGORY_LINKS = [
    ({"operations", "ongoing activities"}, "/countries/{id}/ongoing-activities", "Ongoing Activities"),
    ({"emergencies", "current disasters"}, "/countries/{id}/ongoing-activities/emergencies", "Ongoing Emergencies"),
    ({"red cross activities", "ns activities"}, "/countries/{id}/ns-overview/activities", "National Society Activities"),
    ({"red cross structure", "branches"}, "/countries/{id}/ns-overview/context-and-structure", "Context and Structure"),
    (
        {"country plan", "strategy", "annual plan", "unified plan"},
        "/countries/{id}/ns-overview/strategic-priorities",
        "Strategic Priorities",
    ),
    ({"capacity", "per", "response capacity"}, "/countries/{id}/ns-overview/capacity", "Capacity"),
    ({"partners", "movement partners"}, "/countries/{id}/ns-overview/partners", "Partners"),
    ({"profile", "demographics", "risk profile", "humanitarian context"}, "/countries/{id}/profile/overview", "Country Profile"),
]


def _get_country_name_to_id_map() -> dict:
    """Returns a cached {lowercased name or ISO3: id} map for independent, non-deprecated countries"""
    from django.core.cache import cache

    from api.models import Country

    name_to_id = cache.get(COUNTRY_SEARCH_CACHE_KEY)
    if name_to_id is not None:
        return name_to_id

    name_to_id = {}
    for country_id, name, iso3 in Country.objects.filter(is_deprecated=False).values_list("id", "name", "iso3"):
        if name:
            name_to_id[name.strip().lower()] = country_id
        if iso3:
            name_to_id[iso3.strip().lower()] = country_id

    cache.set(COUNTRY_SEARCH_CACHE_KEY, name_to_id, timeout=COUNTRY_SEARCH_CACHE_TIMEOUT_SECONDS)
    return name_to_id


def get_country_specific_search_urls(phrase: str) -> list[dict]:
    """Returns pre-defined {url, name} entries for phrases like "<country> emergencies" (country matched by name or ISO3)"""
    if not phrase:
        return []
    normalized_phrase = phrase.strip().lower()
    name_to_id = _get_country_name_to_id_map()

    # Longest country token first, so e.g. "nigeria" isn't shadowed by "niger".
    for country_token in sorted(name_to_id, key=len, reverse=True):
        if normalized_phrase.startswith(country_token + " "):
            remainder = normalized_phrase[len(country_token) + 1 :].strip()
        elif normalized_phrase.endswith(" " + country_token):
            remainder = normalized_phrase[: -(len(country_token) + 1)].strip()
        else:
            continue

        country_id = name_to_id[country_token]
        return [
            {"url": template.format(id=country_id), "name": name}
            for expressions, template, name in COUNTRY_CATEGORY_LINKS
            if remainder in expressions
        ]
    return []


# FIXME: not usable because of circular dependency
# def filter_visibility_by_auth(user, visibility_model_class):
#     if user.is_authenticated:
#         if is_user_ifrc(user):
#             return visibility_model_class.objects.all()
#         else:
#             return visibility_model_class.objects.exclude(visibility=VisibilityChoices.IFRC)
#     return visibility_model_class.objects.filter(visibility=VisibilityChoices.PUBLIC)


def get_model_name(model):
    return f"{model._meta.app_label}.{model.__name__}"


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def bad_request(message):
    return JsonResponse({"statusCode": 400, "error_message": message}, status=400)


def generate_field_report_title(
    country: "Country",
    dtype: "DisasterType",
    event: "Event",
    start_date: Optional[timezone.datetime],
    title: str,
    is_covid_report: bool = False,
    id: Optional[int] = None,
):
    """
    Generates the summary based on the country, dtype, event, start_date, title and is_covid_report
    """
    from api.models import FieldReport

    current_date = timezone.now().strftime("%Y-%m-%d")
    # NOTE: start_date is optional and setting it to current date if not provided
    if start_date:
        start_date = start_date.strftime("%m-%Y")
    else:
        start_date = timezone.now().strftime("%m-%Y")
    current_fr_number = (
        FieldReport.objects.filter(event=event, countries__id=country.id).aggregate(max_fr_num=models.Max("fr_num"))["max_fr_num"]
        or 0
    )
    fr_num = current_fr_number + 1

    # NOTE: Checking if event or country is changed while Updating
    if id:
        fr = get_object_or_404(FieldReport, id=id)
        if fr.event == event and fr.countries.first() == country:
            fr_num = current_fr_number

    suffix = ""
    if fr_num > 1 and event:
        suffix = f"#{fr_num} ({current_date})"
    if is_covid_report:
        summary = f"{country.iso3}: COVID-19 {suffix}"
    else:
        summary = f"{country.iso3}: {dtype.name} - {start_date} - {title} {suffix}"
    return summary


class RegionValidator(TypedDict):
    region: int
    local_unit_types: list[int]


class CountryValidator(TypedDict):
    country: int
    local_unit_types: list[int]


def generate_eap_export_url(
    registration_id: int,
    version: Optional[int] = None,
    diff: bool = False,
    summary: bool = False,
) -> str:
    """
    Generate EAP export URL for given registration ID, version and diff flag.
    """
    from django.conf import settings

    from eap.models import EAPRegistration, EAPType

    registration = EAPRegistration.objects.filter(id=registration_id).first()
    if not registration:
        raise ValueError("EAP Registration with the given ID does not exist.")

    url = f"{settings.GO_WEB_INTERNAL_URL}/eap/{registration_id}/export/"
    if summary:
        return url + "summary/"

    assert registration.get_eap_type_enum is not None, "EAP Type should not be None"
    if registration.get_eap_type_enum == EAPType.SIMPLIFIED_EAP:
        url += "simplified/"
    else:
        url += "full/"

    if version:
        url += f"?version={version}"

    # NOTE: EAP exports with diff view only for EAPs exports
    if diff:
        url += "&diff=true" if version else "?diff=true"

    return url
