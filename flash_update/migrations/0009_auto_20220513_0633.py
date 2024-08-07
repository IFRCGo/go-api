# Generated by Django 2.2.28 on 2022-05-13 06:33

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flash_update", "0008_auto_20220311_1023"),
    ]

    operations = [
        migrations.AlterField(
            model_name="flashaction",
            name="organizations",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    choices=[("NTLS", "National Society"), ("PNS", "RCRC"), ("FDRN", "Federation"), ("GOV", "Government")],
                    max_length=4,
                ),
                blank=True,
                default=list,
                size=None,
                verbose_name="organizations",
            ),
        ),
        migrations.AlterField(
            model_name="flashactionstaken",
            name="organization",
            field=models.CharField(
                choices=[("NTLS", "National Society"), ("PNS", "RCRC"), ("FDRN", "Federation"), ("GOV", "Government")],
                max_length=16,
                verbose_name="organization",
            ),
        ),
        migrations.AlterField(
            model_name="flashcountrydistrict",
            name="district",
            field=models.ManyToManyField(blank=True, related_name="flash_district", to="api.District", verbose_name="district"),
        ),
    ]
