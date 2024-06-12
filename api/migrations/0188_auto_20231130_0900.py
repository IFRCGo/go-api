# Generated by Django 3.2.23 on 2023-11-30 09:00

from django.db import migrations


class Migration(migrations.Migration):
    def migrate_event_type(apps, schema_editor):
        GDACSEvent = apps.get_model("api", "GDACSEvent")
        DisasterType = apps.get_model("api", "DisasterType")
        event_type_map = {
            "EQ": "Earthquake",
            "TC": "Cyclone",
            "FL": "Flood",
            "DR": "Drought",
            "WF": "Fire",
            "VO": "Volcanic Eruption",
        }
        for gdacs_event in GDACSEvent.objects.all():
            gdacs_event.disaster_type, created = DisasterType.objects.get_or_create(
                name=event_type_map.get(gdacs_event.event_type)
            )
            gdacs_event.save()

    dependencies = [
        ("api", "0187_gdacsevent_disaster_type"),
    ]

    operations = [migrations.RunPython(migrate_event_type, reverse_code=migrations.RunPython.noop)]
