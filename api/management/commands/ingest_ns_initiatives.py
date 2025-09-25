import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from sentry_sdk.crons import monitor

from api.logger import logger
from api.models import (
    Country,
    CronJob,
    CronJobStatus,
    NSDInitiatives,
    NSDInitiativesCategory,
)
from main.sentry import SentryMonitor

DEFAULT_COUNTRY_ID = 289  # IFRC


def get_country(element):
    country = Country.objects.filter(iso__iexact=element["ISO"]).first()
    if not country:  # Fallback to IFRC, but this does not happen in practice
        country = Country.objects.get(pk=DEFAULT_COUNTRY_ID)
    return country


def get_funding_period(element):
    funding_period = element.get("FundingPeriodInMonths")
    if funding_period is None and element.get("FundingPeriodInYears") is not None:
        funding_period = element["FundingPeriodInYears"] * 12
    return funding_period


def get_defaults(element, country, funding_period, lang):
    defaults = {
        "country": country,
        "year": element.get("Year"),
        "fund_type": (
            f"{element.get('Fund')} – {element.get('FundingType')}" if element.get("FundingType") else element.get("Fund")
        ),
        "allocation": element.get("AllocationInCHF"),
        "funding_period": funding_period,
        "translation_module_original_language": lang,
        "translation_module_skip_auto_translation": True,
    }
    title_field = f"title_{lang}"
    risk_field = f"nsia_risk_{lang}"
    defaults[title_field] = element.get("InitiativeTitle")
    defaults[risk_field] = element.get("Risk")
    return defaults, title_field, risk_field


class Command(BaseCommand):
    help = "Add ns initiatives"

    @monitor(monitor_slug=SentryMonitor.INGEST_NS_INITIATIVES)
    @transaction.atomic
    def handle(self, *args, **kwargs):
        logger.info("Starting NS Inititatives")
        production = settings.GO_ENVIRONMENT == "production"
        # Requires string1|string2|string3 for the three subsystems (NSIA, ESF, CBF):
        api_keys = settings.NS_INITIATIVES_API_KEY.split("|")
        if len(api_keys) != 3:
            logger.info("No proper api-keys are provided. Quitting.")
            return

        LANGUAGES = ["en", "es", "fr", "ar"]
        urls = []

        # Build URLs for all languages and all subsystems
        for lang in LANGUAGES:
            if production:
                urls += [
                    f"https://data.ifrc.org/NSIA_API/api/approvedApplications?languageCode={lang}&apiKey={api_keys[0]}",
                    f"https://data.ifrc.org/ESF_API/api/approvedApplications?languageCode={lang}&apiKey={api_keys[1]}",
                    f"https://data.ifrc.org/CBF_API/api/approvedApplications?languageCode={lang}&apiKey={api_keys[2]}",
                ]
            else:
                urls += [
                    f"https://data-staging.ifrc.org/NSIA_API/api/approvedApplications?languageCode={lang}&apiKey={api_keys[0]}",
                    f"https://data-staging.ifrc.org/ESF_API/api/approvedApplications?languageCode={lang}&apiKey={api_keys[1]}",
                    f"https://data-staging.ifrc.org/CBF_API/api/approvedApplications?languageCode={lang}&apiKey={api_keys[2]}",
                ]

        responses = []
        # Fetch all responses and pair them with their language
        for url in urls:
            lang = url.split("languageCode=")[1].split("&")[0]
            response = requests.get(url)
            if response.status_code == 200:
                responses.append((lang, response.json()))

        added = 0
        updated_remote_ids = set()
        created_ns_initiatives_pk = []

        for lang, resp in responses:
            for element in resp:
                try:
                    remote_id = int(element["Id"]) if element.get("Id") is not None else None
                except (ValueError, TypeError):
                    logger.warning(f"Invalid Id value for element: {element.get('Id')!r}. Skipping element.")
                    continue
                if not remote_id:
                    continue

                country = get_country(element)
                funding_period = get_funding_period(element)
                defaults, title_field, risk_field = get_defaults(element, country, funding_period, lang)

                if lang == "en":
                    ni, created = NSDInitiatives.objects.get_or_create(
                        remote_id=remote_id,
                        defaults=defaults,
                    )
                    if created:
                        added += 1
                    else:
                        for field, value in defaults.items():
                            setattr(ni, field, value)
                        ni.save(update_fields=defaults.keys())
                        updated_remote_ids.add(remote_id)  # Mark as updated, only for EN entries
                    created_ns_initiatives_pk.append(ni.pk)
                else:
                    try:
                        # We could use ISO also to identify the entry, but remote_id is more robust
                        ni = NSDInitiatives.objects.get(remote_id=remote_id)
                        setattr(ni, title_field, element.get("InitiativeTitle"))
                        setattr(ni, risk_field, element.get("Risk"))
                        ni.save(update_fields=[title_field, risk_field])
                    except NSDInitiatives.DoesNotExist:
                        # Should not happen – only if EN entry is missing
                        ni = NSDInitiatives.objects.create(
                            remote_id=remote_id,
                            **defaults,
                        )
                        added += 1
                        created_ns_initiatives_pk.append(ni.pk)
                        logger.warning(f"Created non-EN entry: {remote_id} / {lang}")

                # Handle categories (language-aware)
                raw_categories = element.get("Categories") or []
                if isinstance(raw_categories, (list, tuple)):
                    cat_objs = []
                    for c in raw_categories:
                        if not c:
                            continue
                        name = str(c).strip()
                        if not name:
                            continue
                        # Create / fetch category for this specific language
                        obj, _ = NSDInitiativesCategory.objects.get_or_create(
                            name=name,
                            lang=lang,
                        )
                        cat_objs.append(obj)

                    if cat_objs:
                        ni.categories.add(*cat_objs)

        # Remove old entries not present in the latest fetch
        NSDInitiatives.objects.exclude(id__in=created_ns_initiatives_pk).delete()

        updated = len(updated_remote_ids)
        if added:
            text_to_log = f"{added} NS initiatives added, {updated} updated"
        else:
            text_to_log = f"{updated} NS initiatives updated, no new initiatives added"
        logger.info(text_to_log)
        body = {
            "name": "ingest_ns_initiatives",
            "message": text_to_log,
            "num_result": added + updated,
            "status": CronJobStatus.SUCCESSFUL,
        }
        CronJob.sync_cron(body)
