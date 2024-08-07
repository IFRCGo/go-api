# Generated by Django 4.2.13 on 2024-07-12 06:26

from django.db import migrations


def delete_ids(apps, schema_editor):
    CountryCapacityStrengthening = apps.get_model("api", "CountryCapacityStrengthening")
    CountryCapacityStrengthening.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0211_alter_countrydirectory_unique_together_and_more"),
    ]

    operations = [
        migrations.RunPython(delete_ids, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name="countrycapacitystrengthening",
            unique_together={("assessment_type", "assessment_code")},
        ),
    ]
