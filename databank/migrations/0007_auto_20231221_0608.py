# Generated by Django 3.2.23 on 2023-12-21 06:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('databank', '0006_acapsseasonalcalender'),
    ]

    operations = [
        migrations.AddField(
            model_name='countryoverview',
            name='people_age_13_17',
            field=models.IntegerField(blank=True, null=True, verbose_name='People age 13 to 17'),
        ),
        migrations.AddField(
            model_name='countryoverview',
            name='people_age_18_29',
            field=models.IntegerField(blank=True, null=True, verbose_name='People age 18 to 29'),
        ),
        migrations.AddField(
            model_name='countryoverview',
            name='people_age_6_12',
            field=models.IntegerField(blank=True, null=True, verbose_name='People age 6 to 12'),
        ),
    ]