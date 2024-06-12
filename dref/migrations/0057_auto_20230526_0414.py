# Generated by Django 3.2.19 on 2023-05-26 04:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dref", "0056_auto_20230418_0703"),
    ]

    operations = [
        migrations.AddField(
            model_name="dreffinalreport",
            name="status",
            field=models.IntegerField(
                blank=True, choices=[(0, "In Progress"), (1, "Completed")], null=True, verbose_name="status"
            ),
        ),
        migrations.AddField(
            model_name="drefoperationalupdate",
            name="status",
            field=models.IntegerField(
                blank=True, choices=[(0, "In Progress"), (1, "Completed")], null=True, verbose_name="status"
            ),
        ),
    ]
