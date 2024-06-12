# Generated by Django 2.2.24 on 2021-11-17 15:29

from django.db import migrations, models

import api.models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0135_usercountry"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="visibility",
            field=models.IntegerField(default=1, choices=api.models.VisibilityChoices.choices, verbose_name="visibility"),
        ),
    ]
