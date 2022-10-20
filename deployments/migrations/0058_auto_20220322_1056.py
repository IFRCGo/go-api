# Generated by Django 2.2.27 on 2022-03-22 10:56

import deployments.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deployments', '0057_merge_20220318_0527'),
    ]

    operations = [
        migrations.AddField(
            model_name='emergencyprojectactivity',
            name='has_no_data_on_people_reached',
            field=models.BooleanField(default=False, verbose_name='has_no_data_on_people_reached'),
        ),
        migrations.AlterField(
            model_name='emergencyproject',
            name='status',
            field=models.CharField(choices=[('on_going', 'Ongoing'), ('complete', 'Complete'), ('planned', 'Planned')], default=deployments.models.EmergencyProject.ActivityStatus('on_going'), max_length=40),
        ),
    ]
