# Generated by Django 3.2.23 on 2023-12-12 08:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0189_auto_20231212_0434"),
    ]

    operations = [
        migrations.CreateModel(
            name="CountryDirectory",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(blank=True, max_length=255, null=True, verbose_name="First Name")),
                ("last_name", models.CharField(blank=True, max_length=255, null=True, verbose_name="Last Name")),
                ("position", models.CharField(blank=True, max_length=255, null=True, verbose_name="Position")),
                (
                    "country",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="api.country", verbose_name="Country"),
                ),
            ],
        ),
    ]
