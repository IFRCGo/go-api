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
        {"surge deployments", "active deployments", "deployed staff", "rapid response deployment"},
        "/surge/active-surge-deployments",
    ),
    (
        {"surge", "surge dashboard", "rapid response"},
        "/surge/overview",
    ),
    (
        {"rapid response personnel", "surge staff", "surge roster", "deployable personnel"},
        "/surge/overview/rapid-response-personnel",
    ),
    (
        {"eru", "emergency response unit", "eru deployment", "eru capacity"},
        "/surge/overview/emergency-response-unit",
    ),
    (
        {"surge alerts", "open surge positions", "deployment vacancies", "rapid response alerts"},
        "/alerts/all",
    ),
    (
        {"deployed personnel", "all deployments", "rapid response deployments"},
        "/deployed-personnels/all",
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
    ),
    (
        {"surge catalogue", "catalogue of surge services", "surge roles", "role profiles", "erus", "technical competencies"},
        "/surge/catalogue/overview",
    ),
    (
        {"administration", "admin support"},
        "/surge/catalogue/administration",
    ),
    (
        {"cva", "cash assistance", "cash transfer programming", "vouchers"},
        "/surge/catalogue/cash",
    ),
    (
        {"cmr", "civil military relations"},
        "/surge/catalogue/other/civil-military-relations",
    ),
    (
        {"communications", "media", "public information"},
        "/surge/catalogue/communication",
    ),
    (
        {"cea", "community engagement", "accountability to affected people", "aap"},
        "/surge/catalogue/community-engagement",
    ),
    (
        {"digital surge", "it support", "humanitarian technology", "ict"},
        "/surge/catalogue/digital-systems",
    ),
    (
        {"drr", "disaster risk reduction", "resilience"},
        "/surge/catalogue/other/disaster-risk-reduction",
    ),
    (
        {"drones", "uav", "aerial imagery", "drone mapping"},
        "/surge/catalogue/other/uav",
    ),
    (
        {"needs assessment", "rapid assessment", "initial assessment"},
        "/surge/catalogue/emergency-needs-assessment",
    ),
    (
        {"green response", "environmental sustainability"},
        "/surge/catalogue/other/green-response",
    ),
    (
        {"health surge", "emergency health", "public health"},
        "/surge/catalogue/health",
    ),
    (
        {"humanitarian diplomacy", "hd", "advocacy"},
        "/surge/catalogue/other/humanitarian-diplomacy",
    ),
    (
        {"human resources", "hr surge", "people management"},
        "/surge/catalogue/other/human-resources",
    ),
    (
        {"information management", "im", "data analysis", "mapping", "gis", "geospatial", "dashboards"},
        "/surge/catalogue/information-management",
    ),
    (
        {"idrl", "disaster law", "legal preparedness"},
        "/surge/catalogue/other/international-disaster-response-law",
    ),
    (
        {"livelihoods", "basic needs", "lbn", "food security"},
        "/surge/catalogue/livelihood",
    ),
    (
        {"logistics", "supply chain", "procurement", "fleet", "warehousing"},
        "/surge/catalogue/logistics",
    ),
    (
        {"migration", "displacement", "migrants"},
        "/surge/catalogue/other/migration",
    ),
    (
        {"nsd", "national society development", "branch development"},
        "/surge/catalogue/other/national-society-development",
    ),
    (
        {"operations management", "operations manager", "field coordinator"},
        "/surge/catalogue/operations-management",
    ),
    (
        {"operations support hub", "osh", "basecamp"},
        "/surge/catalogue/basecamp",
    ),
    (
        {"pmer", "monitoring and evaluation", "reporting", "m&e"},
        "/surge/catalogue/pmer",
    ),
    (
        {"per", "preparedness assessment"},
        "/surge/catalogue/other/preparedness-effective-response",
    ),
    (
        {"pgi", "protection gender inclusion", "safeguarding", "disability inclusion"},
        "/surge/catalogue/pgi",
    ),
    (
        {"recovery", "early recovery", "recovery planning"},
        "/surge/catalogue/other/recovery",
    ),
    (
        {"relief", "relief distribution", "nfi", "household items"},
        "/surge/catalogue/relief",
    ),
    (
        {"risk management", "operational risk"},
        "/surge/catalogue/risk-management",
    ),
    (
        {"security", "field security", "safety and security"},
        "/surge/catalogue/security",
    ),
    (
        {"shelter", "emergency shelter", "settlements"},
        "/surge/catalogue/shelter",
    ),
    (
        {"sprm", "resource mobilisation", "donor relations", "fundraising", "funding coverage"},
        "/surge/catalogue/other/strategic-partnership-resource-mobilisation",
    ),
    (
        {"wash", "water sanitation hygiene", "hygiene promotion"},
        "/surge/catalogue/wash",
    ),
    (
        {"risk watch", "seasonal risk", "forecast", "climate risk", "hazard monitoring"},
        "/risk-watch/seasonal",
    ),
    (
        {"preparedness resources", "preparedness tools", "ns preparedness"},
        "/preparedness/resources-catalogue",
    ),
    (
        {"per global summary", "preparedness overview", "preparedness assessment results"},
        "/preparedness/global-summary",
    ),
    (
        {"per performance", "preparedness performance", "response capacity"},
        "/preparedness/global-performance",
    ),
    (
        {"emergencies", "active emergencies", "disasters", "current crises"},
        "/emergencies/all",
    ),
    (
        {"operations", "appeals", "emergency appeals", "dref operations", "response funding"},
        "/appeals/all",
    ),
    (
        {"operational learning", "learn", "lessons learned", "after action review", "aar", "evaluations"},
        "/operational-learning",
    ),
    (
        {"survey designer", "questionnaire builder", "form designer", "survey builder", "xlsform", "data collection form"},
        "https://surveydesigner.ifrc.org/",
    ),
    (
        {"wiki", "go wiki", "go documentation", "user guide", "help", "how to use go", "go guidance"},
        "https://go-wiki.ifrc.org/en/home",
    ),
    (
        {"go blog", "go news", "go updates", "product updates", "new go features"},
        "https://ifrcgoproject.medium.com/",
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
    ),
    (
        {"montandon data", "global crisis databank", "methodology", "partners", "disaster data platform"},
        "https://montandondata.org/",
    ),
    (
        {"montandon notebooks", "cookbook", "disaster analytics", "stac notebooks", "python disaster data", "jupyter"},
        "https://ifrcgo.org/montandon-notebooks/",
    ),
    (
        {"register go", "create go account", "sign up", "access go"},
        "/register",
    ),
    (
        {"go source code", "github", "open source", "go repository", "developer resources"},
        "https://github.com/ifrcgo",
    ),
    (
        {"go api", "api documentation", "developer api", "data api", "integration", "endpoints"},
        "https://go-api.ifrc.org/docs/",
    ),
    (
        {"kobo", "kobotoolbox", "mobile data collection", "field data collection", "surveys"},
        "https://kobo.ifrc.org/",
    ),
    (
        {"kobo faq", "kobo help", "kobo guidance", "data collection help"},
        "https://www.ifrc.org/ifrc-kobo",
    ),
]


def get_predefined_search_url(phrase: str) -> Optional[str]:
    """Returns the pre-defined URL for a known search phrase, or None if there is no match"""
    if not phrase:
        return None
    normalized_phrase = phrase.strip().lower()
    for expressions, url in SEARCH_PREDEFINED_LINKS:
        if normalized_phrase in expressions:
            return url
    return None


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
