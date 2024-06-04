# Generated by Django 3.2.23 on 2023-12-12 10:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0190_countrydirectory"),
    ]

    operations = [
        migrations.CreateModel(
            name="CountryKeyDocument",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="Name")),
                ("url", models.CharField(max_length=255, verbose_name="Url")),
                ("thumbnail", models.CharField(max_length=255, verbose_name="Thumbnail")),
                ("document_type", models.CharField(max_length=255, verbose_name="Document Type")),
                ("year", models.DateField(verbose_name="Year")),
                (
                    "country",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="api.country", verbose_name="Country"),
                ),
            ],
        ),
    ]
