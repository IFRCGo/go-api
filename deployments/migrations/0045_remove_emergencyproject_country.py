# Generated by Django 2.2.27 on 2022-03-06 12:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0044_auto_20220305_0922"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="emergencyproject",
            name="country",
        ),
    ]
