import base64
import typing
from typing import Optional

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
        if fr.fr_num and fr.event == event and fr.countries.first() == country:
            fr_num = fr.fr_num

    suffix = ""
    if fr_num > 1 and event:
        suffix = f"#{fr_num} ({current_date})"
    if is_covid_report:
        summary = f"{country.iso3}: COVID-19 {suffix}"
    else:
        summary = f"{country.iso3}: {dtype.name} - {start_date} - {title} {suffix}"
    return summary
