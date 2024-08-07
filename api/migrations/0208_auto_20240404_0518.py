# Generated by Django 3.2.25 on 2024-04-04 05:18

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0207_auto_20240311_1044"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="country",
            name="email",
        ),
        migrations.AddField(
            model_name="country",
            name="emails",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Email"),
                blank=True,
                default=list,
                null=True,
                size=None,
            ),
        ),
    ]
