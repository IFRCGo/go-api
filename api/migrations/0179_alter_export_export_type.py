# Generated by Django 3.2.20 on 2023-09-12 05:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0178_auto_20230911_0923"),
    ]

    operations = [
        migrations.AlterField(
            model_name="export",
            name="export_type",
            field=models.CharField(
                choices=[
                    ("dref-applications", "Dref Applications"),
                    ("dref-ops-updates", "Dref Operational Updates"),
                    ("dref-final-reports", "Dref Final Reports"),
                ],
                max_length=255,
                verbose_name="Export Type",
            ),
        ),
    ]
