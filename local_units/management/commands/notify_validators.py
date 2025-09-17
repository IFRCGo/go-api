from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from local_units.models import LocalUnit, Validator
from local_units.utils import (
    get_email_context,
    get_local_unit_global_validators,
    get_local_unit_region_validators,
)

# from main.sentry import SentryMonitor
from notifications.notification import send_notification

# from sentry_sdk.crons import monitor


class Command(BaseCommand):
    help = "Notify validators for the pending local units in different period of time"

    # @monitor(monitor_slug=SentryMonitor.NOTIFY_VALIDATORS) # NOTE: Disabled for now
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Notifying the validators..."))
        # NOTE: In production use standard email notification time(7days/14days),shorter delays(1day/2days) elsewhere for testing
        production = settings.GO_ENVIRONMENT == "production"
        if production:
            regional_email_notification_days = 7
            global_email_notification_days = 14
        else:
            regional_email_notification_days = 1
            global_email_notification_days = 2
        # Regional Validators: 14 days
        queryset_for_regional_validators = LocalUnit.objects.filter(
            status__in=[LocalUnit.Status.UNVALIDATED, LocalUnit.Status.PENDING_EDIT_VALIDATION],
            is_deprecated=False,
            last_sent_validator_type=Validator.LOCAL,
            created_at__lte=timezone.now() - timedelta(days=regional_email_notification_days),
        )

        # Global Validators: 28 days
        queryset_for_global_validators = LocalUnit.objects.filter(
            status__in=[LocalUnit.Status.UNVALIDATED, LocalUnit.Status.PENDING_EDIT_VALIDATION],
            is_deprecated=False,
            last_sent_validator_type=Validator.REGIONAL,
            created_at__lte=timezone.now() - timedelta(days=global_email_notification_days),
        )

        for local_unit in queryset_for_regional_validators:
            self.stdout.write(self.style.NOTICE(f"Notifying regional validators for local unit pk:({local_unit.id})"))
            email_context = get_email_context(local_unit)
            email_context["is_validator_regional_admin"] = True
            email_subject = "Action Required: Local Unit Pending Validation"
            email_type = "Local Unit"

            for region_admin_validator in get_local_unit_region_validators(local_unit):
                if not region_admin_validator.email:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping regional validator {region_admin_validator.get_full_name()} for local unit pk:({local_unit.id}) because email is missing."  # noqa
                        )
                    )
                    continue
                try:
                    email_context["full_name"] = region_admin_validator.get_full_name()
                    email_body = render_to_string("email/local_units/local_unit.html", email_context)
                    send_notification(email_subject, region_admin_validator.email, email_body, email_type)
                    local_unit.last_sent_validator_type = Validator.REGIONAL
                    local_unit.save(update_fields=["last_sent_validator_type"])
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Failed to notify regional validator {region_admin_validator.get_full_name()} for local unit pk:({local_unit.id}): {e}"  # noqa
                        )
                    )
                    continue

        for local_unit in queryset_for_global_validators:
            self.stdout.write(self.style.NOTICE(f"Notifying global validators for local unit pk:({local_unit.id})"))
            email_context = get_email_context(local_unit)
            email_context["is_validator_global_admin"] = True
            email_subject = "Action Required: Local Unit Pending Validation"
            email_type = "Local Unit"

            for global_validator in get_local_unit_global_validators(local_unit):
                if not global_validator.email:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping global validator {global_validator.get_full_name()} for local unit:({local_unit.id}) because email is missing."  # noqa
                        )
                    )
                    continue
                try:
                    email_context["full_name"] = global_validator.get_full_name()
                    email_body = render_to_string("email/local_units/local_unit.html", email_context)
                    send_notification(email_subject, global_validator.email, email_body, email_type)
                    local_unit.last_sent_validator_type = Validator.GLOBAL
                    local_unit.save(update_fields=["last_sent_validator_type"])
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Failed to notify global validator {global_validator.get_full_name()} for local unit pk:({local_unit.id}): {e}"  # noqa
                        )
                    )
                    continue

        self.stdout.write(self.style.SUCCESS("Successfully sent the notifications to the validators"))
