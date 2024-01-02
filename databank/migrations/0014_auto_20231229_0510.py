# Generated by Django 3.2.23 on 2023-12-29 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('databank', '0013_auto_20231228_1038'),
    ]

    operations = [
        migrations.AddField(
            model_name='countryoverview',
            name='world_bank_gdp',
            field=models.IntegerField(blank=True, null=True, verbose_name='world bank gdp'),
        ),
        migrations.AddField(
            model_name='countryoverview',
            name='world_bank_gender_inequality_index',
            field=models.IntegerField(blank=True, null=True, verbose_name='world bank gender inequality index'),
        ),
        migrations.AddField(
            model_name='countryoverview',
            name='world_bank_gni',
            field=models.IntegerField(blank=True, null=True, verbose_name='world bank gni'),
        ),
        migrations.AddField(
            model_name='countryoverview',
            name='world_bank_life_expectancy',
            field=models.IntegerField(blank=True, null=True, verbose_name='world bank life expectancy'),
        ),
        migrations.AddField(
            model_name='countryoverview',
            name='world_bank_literacy_rate',
            field=models.IntegerField(blank=True, null=True, verbose_name='world bank life expectancy'),
        ),
        migrations.AddField(
            model_name='countryoverview',
            name='world_bank_population',
            field=models.IntegerField(blank=True, null=True, verbose_name='world bank population'),
        ),
        migrations.AddField(
            model_name='countryoverview',
            name='world_bank_population_above_age_65',
            field=models.IntegerField(blank=True, null=True, verbose_name='world bank population above age 65'),
        ),
        migrations.AddField(
            model_name='countryoverview',
            name='world_bank_population_age_14',
            field=models.IntegerField(blank=True, null=True, verbose_name='world bank population age 14'),
        ),
        migrations.AddField(
            model_name='countryoverview',
            name='world_bank_urban_population_percentage',
            field=models.IntegerField(blank=True, null=True, verbose_name='world bank urban population percentage'),
        ),
    ]
