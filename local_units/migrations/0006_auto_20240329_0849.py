# Generated by Django 3.2.25 on 2024-03-29 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("local_units", "0005_delegationoffice_delegationofficetype"),
    ]

    operations = [
        migrations.AddField(
            model_name="localunit",
            name="data_source_id",
            field=models.IntegerField(blank=True, null=True, verbose_name="Data Source Id"),
        ),
        migrations.AlterField(
            model_name="localunit",
            name="city_en",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="City in English"),
        ),
        migrations.AlterField(
            model_name="localunit",
            name="city_loc",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="City in local language"),
        ),
    ]
