# Generated by Django 4.2.19 on 2025-03-03 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("country_plan", "0008_alter_countryplan_internal_plan_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="countryplan",
            name="internal_plan_url",
            field=models.URLField(blank=True, null=True, verbose_name="internal_plan_url"),
        ),
        migrations.AddField(
            model_name="countryplan",
            name="public_plan_url",
            field=models.URLField(blank=True, null=True, verbose_name="public_plan_url"),
        ),
    ]
