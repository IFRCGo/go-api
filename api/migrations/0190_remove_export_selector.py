# Generated by Django 3.2.23 on 2024-01-29 04:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0189_merge_20240117_0551"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="export",
            name="selector",
        ),
    ]
