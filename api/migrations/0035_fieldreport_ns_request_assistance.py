# Generated by Django 2.0.12 on 2019-11-28 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0034_auto_20191128_0846"),
    ]

    operations = [
        migrations.AddField(
            model_name="fieldreport",
            name="ns_request_assistance",
            field=models.BooleanField(default=False),
        ),
    ]
