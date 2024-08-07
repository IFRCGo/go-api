# Generated by Django 2.0.5 on 2018-07-04 17:00

import django.db.models.deletion
from django.db import migrations, models

import api.models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0007_event_updated_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="SituationReportType",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name="situationreport",
            name="visibility",
            field=models.IntegerField(default=3, choices=api.models.VisibilityChoices.choices),
        ),
        migrations.AddField(
            model_name="situationreport",
            name="type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="situation_reports",
                to="api.SituationReportType",
            ),
        ),
    ]
