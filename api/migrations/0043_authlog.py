# Generated by Django 2.2.9 on 2020-02-05 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0042_auto_20200128_1045"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthLog",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=64)),
                ("username", models.CharField(max_length=256, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
