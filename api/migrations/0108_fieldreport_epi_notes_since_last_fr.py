# Generated by Django 2.2.13 on 2021-01-27 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0107_action_tooltip_text"),
    ]

    operations = [
        migrations.AddField(
            model_name="fieldreport",
            name="epi_notes_since_last_fr",
            field=models.TextField(blank=True, null=True, verbose_name="notes"),
        ),
    ]
