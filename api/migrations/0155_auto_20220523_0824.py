# Generated by Django 3.2 on 2022-05-23 08:24

import re

import django.core.validators
from django.db import migrations, models

import api.utils


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0154_merge_20220513_0934"),
    ]

    operations = [
        migrations.AlterField(
            model_name="country",
            name="independent",
            field=models.BooleanField(default=None, help_text="Is this an independent country?", null=True),
        ),
        migrations.AlterField(
            model_name="country",
            name="nsi_annual_fdrs_reporting",
            field=models.BooleanField(blank=True, null=True, verbose_name="Annual Reporting to FDRS"),
        ),
        migrations.AlterField(
            model_name="country",
            name="nsi_cmc_dashboard_compliance",
            field=models.BooleanField(blank=True, null=True, verbose_name="Complying with CMC Dashboard"),
        ),
        migrations.AlterField(
            model_name="country",
            name="nsi_domestically_generated_income",
            field=models.BooleanField(blank=True, null=True, verbose_name=">50% Domestically Generated Income"),
        ),
        migrations.AlterField(
            model_name="country",
            name="nsi_gov_financial_support",
            field=models.BooleanField(blank=True, null=True, verbose_name="Gov Financial Support"),
        ),
        migrations.AlterField(
            model_name="country",
            name="nsi_policy_implementation",
            field=models.BooleanField(blank=True, null=True, verbose_name="Your Policy / Programme Implementation"),
        ),
        migrations.AlterField(
            model_name="country",
            name="nsi_risk_management_framework",
            field=models.BooleanField(blank=True, null=True, verbose_name="Risk Management Framework"),
        ),
        migrations.AlterField(
            model_name="event",
            name="slug",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Optional string for a clean URL. For example, go.ifrc.org/emergency/hurricane-katrina-2019. The string cannot start with a number and is forced to be lowercase. Recommend using hyphens over underscores. Special characters like # is not allowed.",
                max_length=50,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        re.compile("^[-a-zA-Z0-9_]+\\Z"),
                        "Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.",
                        "invalid",
                    ),
                    api.utils.validate_slug_number,
                ],
                verbose_name="slug",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="slug_ar",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Optional string for a clean URL. For example, go.ifrc.org/emergency/hurricane-katrina-2019. The string cannot start with a number and is forced to be lowercase. Recommend using hyphens over underscores. Special characters like # is not allowed.",
                max_length=50,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        re.compile("^[-a-zA-Z0-9_]+\\Z"),
                        "Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.",
                        "invalid",
                    ),
                    api.utils.validate_slug_number,
                ],
                verbose_name="slug",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="slug_en",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Optional string for a clean URL. For example, go.ifrc.org/emergency/hurricane-katrina-2019. The string cannot start with a number and is forced to be lowercase. Recommend using hyphens over underscores. Special characters like # is not allowed.",
                max_length=50,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        re.compile("^[-a-zA-Z0-9_]+\\Z"),
                        "Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.",
                        "invalid",
                    ),
                    api.utils.validate_slug_number,
                ],
                verbose_name="slug",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="slug_es",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Optional string for a clean URL. For example, go.ifrc.org/emergency/hurricane-katrina-2019. The string cannot start with a number and is forced to be lowercase. Recommend using hyphens over underscores. Special characters like # is not allowed.",
                max_length=50,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        re.compile("^[-a-zA-Z0-9_]+\\Z"),
                        "Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.",
                        "invalid",
                    ),
                    api.utils.validate_slug_number,
                ],
                verbose_name="slug",
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="slug_fr",
            field=models.CharField(
                blank=True,
                default=None,
                help_text="Optional string for a clean URL. For example, go.ifrc.org/emergency/hurricane-katrina-2019. The string cannot start with a number and is forced to be lowercase. Recommend using hyphens over underscores. Special characters like # is not allowed.",
                max_length=50,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        re.compile("^[-a-zA-Z0-9_]+\\Z"),
                        "Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.",
                        "invalid",
                    ),
                    api.utils.validate_slug_number,
                ],
                verbose_name="slug",
            ),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="epi_figures_source",
            field=models.IntegerField(
                blank=True,
                choices=[(0, "Ministry of health"), (1, "WHO"), (2, "OTHER")],
                null=True,
                verbose_name="figures source (epidemic)",
            ),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="ns_request_assistance",
            field=models.BooleanField(blank=True, default=None, null=True, verbose_name="NS request assistance"),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="request_assistance",
            field=models.BooleanField(blank=True, default=None, null=True, verbose_name="request assistance"),
        ),
        migrations.AlterField(
            model_name="profile",
            name="org_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("NTLS", "National Society"),
                    ("DLGN", "Delegation"),
                    ("SCRT", "Secretariat"),
                    ("ICRC", "ICRC"),
                    ("OTHR", "Other"),
                ],
                default="OTHR",
                max_length=4,
                verbose_name="organization type",
            ),
        ),
    ]
