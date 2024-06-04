# Generated by Django 2.2.10 on 2020-05-04 13:15

from django.db import migrations, models

import api.models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0064_auto_20200504_0917"),
    ]

    operations = [
        migrations.AddField(
            model_name="fieldreport",
            name="epi_figures_source",
            field=models.IntegerField(blank=True, choices=api.models.EPISourceChoices.choices, default=0, null=True),
        ),
    ]
