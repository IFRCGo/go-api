# Generated by Django 3.2.23 on 2024-01-12 05:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0187_auto_20231218_0508"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("per", "0094_update_supported_by_organization_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="PerDocumentUpload",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="per/documents/", verbose_name="file")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                (
                    "country",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="api.country", verbose_name="country"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created_by",
                    ),
                ),
            ],
        ),
    ]
