# Generated by Django 3.2.20 on 2023-08-04 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0084_auto_20230731_1006"),
    ]

    operations = [
        migrations.AlterField(
            model_name="personnel",
            name="location",
            field=models.CharField(blank=True, max_length=300, null=True, verbose_name="location"),
        ),
    ]
