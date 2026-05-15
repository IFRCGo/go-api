from django.core.management.base import BaseCommand

from api.models import Event


class Command(BaseCommand):
    help = "Update event sources based on name prefix and auto-generated status"

    def handle(self, *args, **options):
        queryset = Event.objects.filter(auto_generated=True, source=0)
        self.stdout.write(
            self.style.NOTICE(
                f"{queryset.count()} events will be assigned a source (GDACS or Manual Input) based on name prefix."
            )
        )
        to_update = []
        for event in queryset.iterator():
            if event.name.startswith("GDACS"):
                event.source = Event.EventSource.GDACS
                self.stdout.write(self.style.NOTICE(f"Updating {event.name} source to {Event.EventSource.GDACS.label}"))
            else:
                event.source = Event.EventSource.MANUAL_INPUT
                self.stdout.write(self.style.NOTICE(f"Updating {event.name} source to {Event.EventSource.MANUAL_INPUT.label}"))
                event.auto_generated = False
            to_update.append(event)

        updated_event = Event.objects.bulk_update(to_update, ["source", "auto_generated"])
        self.stdout.write(self.style.SUCCESS(f"Total {updated_event} Events source have been updated successfully."))
