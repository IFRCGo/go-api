# Generated by Django 3.2.18 on 2023-04-06 04:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0161_alter_event_options'),
        ('deployments', '0077_project_project_admin2'),
    ]

    operations = [
        migrations.AddField(
            model_name='emergencyproject',
            name='admin2',
            field=models.ManyToManyField(blank=True, to='api.Admin2', verbose_name='admin2'),
        ),
    ]
