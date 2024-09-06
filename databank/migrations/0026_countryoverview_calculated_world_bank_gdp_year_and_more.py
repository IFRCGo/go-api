# Generated by Django 4.2.15 on 2024-08-22 11:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("databank", "0025_countryoverview_world_bank_gni_capita"),
    ]

    operations = [
        migrations.RenameField(
            model_name="countryoverview",
            old_name="world_bank_gender_inequality_index",
            new_name="world_bank_gender_equality_index",
        ),
        migrations.AlterField(
            model_name="countryoverview",
            name="world_bank_gender_equality_index",
            field=models.FloatField(blank=True, null=True, verbose_name="world bank gender equality index"),
        ),
        migrations.AddField(
            model_name="countryoverview",
            name="calculated_world_bank_gdp_year",
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name="calculated world bank gdp year"),
        ),
        migrations.AddField(
            model_name="countryoverview",
            name="calculated_world_bank_gender_equality_index_year",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="calculated world bank gender equality index year"
            ),
        ),
        migrations.AddField(
            model_name="countryoverview",
            name="calculated_world_bank_gni_capita_year",
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name="calculated world bank gni capita year"),
        ),
        migrations.AddField(
            model_name="countryoverview",
            name="calculated_world_bank_gni_year",
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name="calculated world bank gni year"),
        ),
        migrations.AddField(
            model_name="countryoverview",
            name="calculated_world_bank_life_expectancy_year",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="calculated world bank life expectancy year"
            ),
        ),
        migrations.AddField(
            model_name="countryoverview",
            name="calculated_world_bank_literacy_rate_year",
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name="calculated world bank literacy rate year"),
        ),
        migrations.AddField(
            model_name="countryoverview",
            name="calculated_world_bank_population_above_age_65_year",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="calculated world bank population above age 65 date in year"
            ),
        ),
        migrations.AddField(
            model_name="countryoverview",
            name="calculated_world_bank_population_age_14_year",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="calculated world bank population age 14 date in year"
            ),
        ),
        migrations.AddField(
            model_name="countryoverview",
            name="calculated_world_bank_population_year",
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name="calculated world bank population year"),
        ),
        migrations.AddField(
            model_name="countryoverview",
            name="calculated_world_bank_poverty_rate_year",
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name="calculated world bank poverty rate year"),
        ),
        migrations.AddField(
            model_name="countryoverview",
            name="calculated_world_bank_urban_population_percentage_year",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="calculated world bank urban population percentage year"
            ),
        ),
    ]
