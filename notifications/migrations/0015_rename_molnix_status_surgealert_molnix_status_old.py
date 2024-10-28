# Generated by Django 4.2.13 on 2024-07-16 08:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0014_surgealert_status"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="surgealert",
            name="molnix_status",
        ),
        migrations.RenameField(
            model_name="surgealert",
            old_name="status",
            new_name="molnix_status",
        ),
        migrations.RemoveField(
            model_name="surgealert",
            name="is_active",
        ),
        migrations.RemoveField(
            model_name="surgealert",
            name="is_stood_down",
        ),
    ]