# Generated by Django 3.2.24 on 2024-03-25 06:11

from django.db import migrations

def update_description_to_null(apps, schema_editor):
    FormComponent = apps.get_model('per', 'FormComponent')
    FormComponent.objects.filter(id__in=[48, 20, 15]).update(
        description=None,
        description_en=None,
        description_fr=None,
        description_es=None,
        description_ar=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('per', '0109_auto_20240320_0804'),
    ]

    operations = [
        migrations.RunPython(
            update_description_to_null,
            reverse_code=migrations.RunPython.noop
        ),
    ]
