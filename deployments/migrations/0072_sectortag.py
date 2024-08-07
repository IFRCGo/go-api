# Generated by Django 3.2.18 on 2023-03-01 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0071_sector"),
    ]

    operations = [
        migrations.CreateModel(
            name="SectorTag",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="title")),
                ("slug", models.CharField(max_length=255, verbose_name="slug")),
                ("order", models.SmallIntegerField(default=0)),
            ],
        ),
    ]
