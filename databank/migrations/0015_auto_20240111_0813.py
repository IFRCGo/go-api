# Generated by Django 3.2.23 on 2024-01-11 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("databank", "0014_auto_20231229_0510"),
    ]

    operations = [
        migrations.AlterField(
            model_name="countryoverview",
            name="world_bank_gdp",
            field=models.FloatField(blank=True, null=True, verbose_name="world bank gdp"),
        ),
        migrations.AlterField(
            model_name="countryoverview",
            name="world_bank_gender_inequality_index",
            field=models.FloatField(blank=True, null=True, verbose_name="world bank gender inequality index"),
        ),
        migrations.AlterField(
            model_name="countryoverview",
            name="world_bank_gni",
            field=models.FloatField(blank=True, null=True, verbose_name="world bank gni"),
        ),
        migrations.AlterField(
            model_name="countryoverview",
            name="world_bank_literacy_rate",
            field=models.FloatField(blank=True, null=True, verbose_name="world bank life expectancy"),
        ),
        migrations.AlterField(
            model_name="countryoverview",
            name="world_bank_urban_population_percentage",
            field=models.FloatField(blank=True, null=True, verbose_name="world bank urban population percentage"),
        ),
    ]
