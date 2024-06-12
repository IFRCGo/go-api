# Generated by Django 2.2.27 on 2022-08-18 09:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0067_merge_0066_auto_20220523_0824_0066_auto_20220727_0708"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnnualSplit",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.IntegerField(blank=True, null=True, verbose_name="year")),
                ("budget_amount", models.IntegerField(blank=True, null=True, verbose_name="amount")),
                ("target_male", models.IntegerField(blank=True, null=True, verbose_name="target male")),
                ("target_female", models.IntegerField(blank=True, null=True, verbose_name="target female")),
                ("target_other", models.IntegerField(blank=True, null=True, verbose_name="target other")),
                ("target_total", models.IntegerField(blank=True, null=True, verbose_name="target total")),
                ("reached_male", models.IntegerField(blank=True, null=True, verbose_name="reached male")),
                ("reached_female", models.IntegerField(blank=True, null=True, verbose_name="reached female")),
                ("reached_other", models.IntegerField(blank=True, null=True, verbose_name="reached other")),
                ("reached_total", models.IntegerField(blank=True, null=True, verbose_name="reached total")),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="annual_splits",
                        to="deployments.Project",
                        verbose_name="project",
                    ),
                ),
            ],
            options={
                "verbose_name": "Annual Split",
                "verbose_name_plural": "Annual Splits",
            },
        ),
    ]
