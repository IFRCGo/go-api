# Generated by Django 3.2.20 on 2023-09-07 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dref", "0068_auto_20230905_0845"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dreffinalreport",
            name="disability_people_per",
            field=models.FloatField(blank=True, null=True, verbose_name="disability people per"),
        ),
        migrations.AlterField(
            model_name="dreffinalreport",
            name="people_per_local",
            field=models.FloatField(blank=True, null=True, verbose_name="people per local"),
        ),
        migrations.AlterField(
            model_name="dreffinalreport",
            name="people_per_urban",
            field=models.FloatField(blank=True, null=True, verbose_name="people per urban"),
        ),
    ]
