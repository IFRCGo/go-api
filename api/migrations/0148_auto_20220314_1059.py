# Generated by Django 2.2.27 on 2022-03-14 10:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0147_auto_20220304_1057"),
    ]

    operations = [
        migrations.AddField(
            model_name="country",
            name="average_household_size",
            field=models.IntegerField(blank=True, null=True, verbose_name="Average Household Size"),
        ),
        migrations.AddField(
            model_name="event",
            name="countries_for_preview",
            field=models.ManyToManyField(
                blank=True, related_name="countries_for_preview", to="api.Country", verbose_name="countries for preview"
            ),
        ),
    ]
