# Generated by Django 3.2.16 on 2023-01-17 10:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0160_merge_0159_auto_20221022_1542_0159_auto_20221028_0940"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="event",
            options={
                "ordering": ("-disaster_start_date", "id"),
                "verbose_name": "emergency",
                "verbose_name_plural": "emergencies",
            },
        ),
    ]
