# Generated by Django 3.2.23 on 2023-12-26 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0196_alter_gdacsevent_severity"),
    ]

    operations = [
        migrations.AddField(
            model_name="country",
            name="founded_date",
            field=models.DateField(blank=True, null=True, verbose_name="Found date"),
        ),
    ]
