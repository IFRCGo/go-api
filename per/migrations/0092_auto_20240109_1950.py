# Generated by Django 3.2.23 on 2024-01-09 19:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("per", "0091_opslearning"),
    ]

    operations = [
        migrations.AddField(
            model_name="opslearning",
            name="organization",
            field=models.IntegerField(
                choices=[(1, "Secretariat"), (2, "National Society")], default=1, verbose_name="organization"
            ),
        ),
        migrations.AddField(
            model_name="opslearning",
            name="organization_validated",
            field=models.IntegerField(
                choices=[(1, "Secretariat"), (2, "National Society")], default=1, verbose_name="organization (validated)"
            ),
        ),
    ]
