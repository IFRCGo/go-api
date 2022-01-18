from django.db.models.functions import Upper
from django.db import migrations, models


def uppercase_iso(apps, schema_editor):
    Country = apps.get_model('api', 'Country')
    District = apps.get_model('api', 'District')

    Country.objects.update(iso3=Upper('iso3'), iso=Upper('iso'))
    District.objects.update(country_iso=Upper('country_iso'))


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0100_auto_20201130_0954'),
    ]

    operations = [
        migrations.RunPython(uppercase_iso),
    ]
