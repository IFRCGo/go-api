# Generated by Django 2.2.13 on 2020-07-21 10:51

from django.core.exceptions import ObjectDoesNotExist
from django.db import migrations, models


def delete_idn(apps, schema_editor):
    District = apps.get_model("api", "District")
    FieldReport = apps.get_model("api", "FieldReport")

    try:
        idn = District.objects.get(id=3525)
        # Find if there are any field reports associated to 3525
        reports = FieldReport.objects.filter(districts__id=3525)
        correct_district = District.objects.get(id=1234)
        for report in reports:
            report.districts.add(correct_district)
            report.districts.remove(3525)

        # Remove the 3525 | Sulawesi Tengah | ID025 | IDN entry from the database, which is a duplicate.
        idn.delete()
    except ObjectDoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0076_auto_20200721_0950"),
    ]

    operations = [
        migrations.RunPython(delete_idn),
    ]
