# Generated by Django 2.2.13 on 2020-11-06 12:22

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("per", "0030_auto_20201106_1205"),
    ]

    operations = [
        migrations.AlterField(
            model_name="overview",
            name="date_of_current_capacity_assessment",
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name="date of current capacity assessment"),
            preserve_default=False,
        ),
    ]
