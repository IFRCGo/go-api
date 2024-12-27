from datetime import timedelta

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone
from sentry_sdk.crons import monitor

from local_units.models import LocalUnit
from local_units.utils import (
    get_email_context,
    get_global_validators,
    get_region_admins,
)
from main.sentry import SentryMonitor
from notifications.notification import send_notification


class Command(BaseCommand):
    help = "Notify validators for the pending local units in different period of time"

    @monitor(monitor_slug=SentryMonitor.NOTIFY_VALIDATORS)
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Notifying the validators..."))

        # Regional Validators: 14 days
        queryset_for_regional_validtors = LocalUnit.objects.filter(
            validated=False, is_deprecated=False, created_at__date=timezone.now() - timedelta(days=14)
        )

        # Global Validators: 28 days
        queryset_for_global_validators = LocalUnit.objects.filter(
            validated=False, is_deprecated=False, created_at__date=timezone.now() - timedelta(days=28)
        )

        for local_unit in queryset_for_regional_validtors:
            self.stdout.write(self.style.NOTICE(f"Notifying regional validators for local unit {local_unit.id}"))

            email_context = get_email_context(local_unit)
            email_context["regional_admin"] = True
            email_subject = "Action Required: Local Unit Pending Validation"
            email_type = "Local Unit"

            for region_admin_validator in get_region_admins(local_unit):
                email_context["full_name"] = region_admin_validator.get_full_name()
                email_body = render_to_string("email/local_units/local_unit.html", email_context)
                send_notification(email_subject, region_admin_validator.email, email_body, email_type)

        for local_unit in queryset_for_global_validators:
            self.stdout.write(self.style.NOTICE(f"Notifying global validators for local unit {local_unit.id}"))
            email_context = get_email_context(local_unit)
            email_context["global_admin"] = True
            email_subject = "Action Required: Local Unit Pending Validation"
            email_type = "Local Unit"

            for global_validator in get_global_validators():
                email_context["full_name"] = global_validator.get_full_name()
                email_body = render_to_string("email/local_units/local_unit.html", email_context)
                send_notification(email_subject, global_validator.email, email_body, email_type)

        self.stdout.write(self.style.SUCCESS("Successfully sent the notifications to the validators"))
