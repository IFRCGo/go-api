# Generated by Django 3.2.19 on 2023-06-15 04:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("per", "0059_auto_20230614_0820"),
    ]

    operations = [
        migrations.AddField(
            model_name="perassessment",
            name="is_draft",
            field=models.BooleanField(blank=True, null=True, verbose_name="is draft"),
        ),
    ]
