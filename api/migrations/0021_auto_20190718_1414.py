# Generated by Django 2.0.12 on 2019-07-18 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0020_auto_20190703_0614"),
    ]

    operations = [
        migrations.AddField(
            model_name="appeal",
            name="previous_update",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="event",
            name="previous_update",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="previous_update",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
