# Generated by Django 3.2.23 on 2024-01-09 05:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0187_auto_20231218_0508"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="event",
            name="slug_ar",
        ),
        migrations.RemoveField(
            model_name="event",
            name="slug_en",
        ),
        migrations.RemoveField(
            model_name="event",
            name="slug_es",
        ),
        migrations.RemoveField(
            model_name="event",
            name="slug_fr",
        ),
    ]
