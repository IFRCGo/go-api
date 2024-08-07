# Generated by Django 2.2.13 on 2020-12-11 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0104_auto_20201210_0910"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="hide_field_report_map",
            field=models.BooleanField(default=False, verbose_name="hide field report map"),
        ),
        migrations.AlterField(
            model_name="event",
            name="hide_attached_field_reports",
            field=models.BooleanField(default=False, verbose_name="hide field report numeric details"),
        ),
    ]
