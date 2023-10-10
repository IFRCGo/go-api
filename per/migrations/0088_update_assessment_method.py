# Generated by Django 3.2.20 on 2023-09-27 08:18

from django.db import migrations


class Migration(migrations.Migration):

    def update_overview_assessment_method(apps, schema_editor):
        Overview = apps.get_model('per', 'Overview')
        overviews = Overview.objects.all()
        for overview in overviews:
            if overview.assessment_method == 'PER':
                overview.assessment_method = 'per'
            elif overview.assessment_method == 'DRCE':
                overview.assessment_method = 'drce'
            else:
                overview.assessment_method = 'per'
            overview.save(update_fields=['assessment_method'])

    dependencies = [
        ('per', '0087_update_phase'),
    ]

    operations = [
        migrations.RunPython(
            update_overview_assessment_method,
            reverse_code=migrations.RunPython.noop
        ),
    ]