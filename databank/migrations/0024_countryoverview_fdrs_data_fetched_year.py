# Generated by Django 3.2.25 on 2024-04-26 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('databank', '0023_auto_20240402_0912'),
    ]

    operations = [
        migrations.AddField(
            model_name='countryoverview',
            name='fdrs_data_fetched_year',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='FDRS Data Fetched Year'),
        ),
    ]