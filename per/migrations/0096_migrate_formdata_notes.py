# Generated by Django 3.2.23 on 2024-01-17 04:55

from django.db import migrations


class Migration(migrations.Migration):

    def migrate_formdata_notes(apps, schema_editor):
        pass

    dependencies = [
        ('per', '0095_perdocumentupload'),
    ]

    operations = [
        migrations.RunPython(
            migrate_formdata_notes,
            reverse_code=migrations.RunPython.noop
        ),
    ]