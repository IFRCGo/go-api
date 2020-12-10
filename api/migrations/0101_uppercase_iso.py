from django.db import migrations, models

def uppercase_iso(apps, schema_editor):
  Country = apps.get_model('api', 'Country')
  for country in Country.objects.all():
    if country.iso:
      country.iso = country.iso.upper()
      country.save()

    if country.iso3:
      country.iso3 = country.iso3.upper()
      country.save()
  
  District = apps.get_model('api', 'District')
  for district in District.objects.all():
    if district.country_iso:
      district.country_iso = district.country_iso.upper()
      district.save()

class Migration(migrations.Migration):
  dependencies = [
    ('api', '0100_auto_20201130_0954'),
  ]

  operations = [
    migrations.RunPython(uppercase_iso),
  ]
