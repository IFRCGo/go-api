# Generated by Django 3.2.23 on 2024-01-17 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("per", "0094_auto_20240116_1845"),
    ]

    operations = [
        migrations.AddField(
            model_name="opslearning",
            name="appeal_document_id",
            field=models.IntegerField(blank=True, null=True, verbose_name="Appeal document ID"),
        ),
    ]
