# Generated by Django 3.2.16 on 2023-01-10 23:01

import django.contrib.gis.db.models.fields
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("api", "0160_merge_0159_auto_20221022_1542_0159_auto_20221028_0940"),
    ]

    operations = [
        migrations.CreateModel(
            name="LocalUnitType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "level",
                    models.IntegerField(
                        validators=[django.core.validators.MaxValueValidator(10), django.core.validators.MinValueValidator(0)],
                        verbose_name="Level",
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="Name")),
            ],
        ),
        migrations.CreateModel(
            name="LocalUnit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("local_branch_name", models.CharField(max_length=255, verbose_name="Branch name in local language")),
                ("english_branch_name", models.CharField(max_length=255, verbose_name="Branch name in English")),
                ("created_at", models.DateTimeField(auto_now=True, verbose_name="Created at")),
                ("modified_at", models.DateTimeField(auto_now=True, verbose_name="Updated at")),
                ("draft", models.BooleanField(default=False, verbose_name="Draft")),
                ("validated", models.BooleanField(default=True, verbose_name="Validated")),
                ("source_en", models.CharField(blank=True, max_length=500, null=True, verbose_name="Source in Local Language")),
                ("source_loc", models.CharField(blank=True, max_length=500, null=True, verbose_name="Source in English")),
                (
                    "address_loc",
                    models.CharField(blank=True, max_length=500, null=True, verbose_name="Address in local language"),
                ),
                ("address_en", models.CharField(blank=True, max_length=500, null=True, verbose_name="Address in English")),
                ("city_loc", models.CharField(max_length=255, verbose_name="City in local language")),
                ("city_en", models.CharField(max_length=255, verbose_name="City in English")),
                (
                    "focal_person_loc",
                    models.CharField(blank=True, max_length=255, null=True, verbose_name="Focal person for local language"),
                ),
                (
                    "focal_person_en",
                    models.CharField(blank=True, max_length=255, null=True, verbose_name="Focal person for English"),
                ),
                ("postcode", models.CharField(max_length=10, null=True, verbose_name="Postal code")),
                ("phone", models.CharField(blank=True, max_length=20, null=True, verbose_name="Telephone")),
                ("email", models.EmailField(blank=True, max_length=255, null=True, verbose_name="Email")),
                ("link", models.URLField(blank=True, max_length=255, null=True, verbose_name="Social link")),
                ("location", django.contrib.gis.db.models.fields.PointField(srid=4326)),
                (
                    "country",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="local_unit_country",
                        to="api.country",
                        verbose_name="Country",
                    ),
                ),
                (
                    "type",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="local_unit_type",
                        to="local_units.localunittype",
                        verbose_name="Type",
                    ),
                ),
            ],
        ),
    ]
