# Generated by Django 3.2.20 on 2023-07-28 04:05

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dref", "0064_dreffinalreport_financial_report_preview"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dref",
            name="modified_at",
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, verbose_name="modified at"),
        ),
        migrations.AlterField(
            model_name="dreffinalreport",
            name="modified_at",
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, verbose_name="modified at"),
        ),
        migrations.AlterField(
            model_name="drefoperationalupdate",
            name="modified_at",
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, verbose_name="modified at"),
        ),
    ]
