# Generated by Django 3.2.23 on 2023-12-26 05:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('databank', '0008_countryoverview_branches'),
    ]

    operations = [
        migrations.AddField(
            model_name='countryoverview',
            name='people_age_60_69',
            field=models.IntegerField(blank=True, null=True, verbose_name='People age 60 to 69'),
        ),
        migrations.AddField(
            model_name='countryoverview',
            name='people_age_70_79',
            field=models.IntegerField(blank=True, null=True, verbose_name='People age 70 to 79'),
        ),
        migrations.AddField(
            model_name='countryoverview',
            name='people_age_80',
            field=models.IntegerField(blank=True, null=True, verbose_name='People age 80'),
        ),
    ]