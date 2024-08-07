# Generated by Django 2.0.12 on 2019-07-08 16:26

import django.db.models.deletion
from django.db import migrations, models

import deployments.models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0020_auto_20190703_0614"),
        ("per", "0007_nsphase"),
    ]

    operations = [
        migrations.CreateModel(
            name="ERUReadiness",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ERU_type", models.IntegerField(default=0, choices=deployments.models.ERUType.choices)),
                ("is_personnel", models.BooleanField(default=False)),
                ("is_equipment", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "national_society",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="api.Country"),
                ),
            ],
            options={
                "verbose_name": "ERU Readiness",
                "verbose_name_plural": "NS-es ERU Readiness",
                "ordering": ("updated_at", "national_society"),
            },
        ),
    ]
