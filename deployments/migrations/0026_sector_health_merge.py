# Generated by Django 2.2.10 on 2020-05-14 10:19

from django.db import migrations


def merge_sector_health(apps, schema_editor):
    """
    Merge Sectors Health (public) and Health (clinical) to Health for Sectors
    """
    Project = apps.get_model("deployments", "Project")

    # This value can change so using value from this time
    HEALTH = 4  # HEALTH_PUBLIC is same as HEALTH in DB
    HEALTH_CLINICAL = 10

    # Migrate all HEALTH_CLINICAL to HEALTH
    Project.objects.filter(primary_sector=HEALTH_CLINICAL).update(primary_sector=HEALTH)


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0025_remove_project_district_20200513_1130"),
    ]

    operations = [
        migrations.RunPython(merge_sector_health),
    ]
