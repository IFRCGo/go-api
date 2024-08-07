# Generated by Django 3.2.20 on 2023-08-16 04:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0171_merge_20230614_0818"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fieldreport",
            name="status",
            field=models.IntegerField(
                choices=[
                    (0, "Unknown"),
                    (2, "Two"),
                    (3, "Three"),
                    (8, "Early Warning / Early Action"),
                    (9, "Event-related"),
                    (10, "Event"),
                ],
                default=0,
                help_text='<a target="_blank" href="/api/v2/fieldreportstatus">Key/value pairs</a>',
                verbose_name="type",
            ),
        ),
    ]
