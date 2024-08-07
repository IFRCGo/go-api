# Generated by Django 2.2.13 on 2021-02-02 18:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0110_auto_20210202_0950"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExternalPartner",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="name")),
            ],
            options={
                "verbose_name": "external partner",
                "verbose_name_plural": "external partners",
            },
        ),
        migrations.CreateModel(
            name="ExternalPartnerCategory",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="name")),
            ],
            options={
                "verbose_name": "external partner category",
                "verbose_name_plural": "external partner caregories",
            },
        ),
        migrations.CreateModel(
            name="SupportedActivity",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="name")),
            ],
            options={
                "verbose_name": "supported activity",
                "verbose_name_plural": "supported activities",
            },
        ),
        migrations.CreateModel(
            name="FieldReportSupportedActivity",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "field_report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="supportedactivities",
                        to="api.FieldReport",
                        verbose_name="field report",
                    ),
                ),
                (
                    "supported_activities",
                    models.ManyToManyField(blank=True, to="api.SupportedActivity", verbose_name="supported activities"),
                ),
            ],
            options={
                "verbose_name": "field report supported activities",
                "verbose_name_plural": "field report supported activities",
            },
        ),
        migrations.CreateModel(
            name="FieldReportExternalPartnerCategory",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "external_partner_categories",
                    models.ManyToManyField(
                        blank=True, to="api.ExternalPartnerCategory", verbose_name="external partner categories"
                    ),
                ),
                (
                    "field_report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="externalpartnercategories",
                        to="api.FieldReport",
                        verbose_name="field report",
                    ),
                ),
            ],
            options={
                "verbose_name": "field report external partner categories",
                "verbose_name_plural": "field report external partner categories",
            },
        ),
        migrations.CreateModel(
            name="FieldReportExternalPartner",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "external_partners",
                    models.ManyToManyField(blank=True, to="api.ExternalPartner", verbose_name="external partners"),
                ),
                (
                    "field_report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="externalpartners",
                        to="api.FieldReport",
                        verbose_name="field report",
                    ),
                ),
            ],
            options={
                "verbose_name": "field report external partners",
                "verbose_name_plural": "field report external partners",
            },
        ),
    ]
