# Generated by Django 4.2.16 on 2024-11-29 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("local_units", "0019_localunitchangerequest_depricated_reason"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="localunitchangerequest",
            name="depricated_reason",
        ),
        migrations.AddField(
            model_name="localunit",
            name="depricated_reason",
            field=models.IntegerField(
                choices=[
                    (1, "Non-existent local unit"),
                    (2, "Incorrectly added local unit"),
                    (3, "Security concerns"),
                    (4, "Other"),
                ],
                default=4,
                verbose_name="Depricated reason",
            ),
        ),
        migrations.AddField(
            model_name="localunit",
            name="depricated_reason_overview",
            field=models.TextField(blank=True, verbose_name="Explain the reason why the local unit is being deleted"),
        ),
    ]
