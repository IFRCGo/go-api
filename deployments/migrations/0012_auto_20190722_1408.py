# Generated by Django 2.0.12 on 2019-07-22 14:08

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0011_erureadiness"),
    ]

    operations = [
        migrations.AddField(
            model_name="personneldeployment",
            name="created_at",
            field=models.DateTimeField(default=datetime.datetime(2017, 8, 21, 14, 8, 50, 306044, tzinfo=utc)),
        ),
        migrations.AddField(
            model_name="personneldeployment",
            name="previous_update",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="personneldeployment",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
