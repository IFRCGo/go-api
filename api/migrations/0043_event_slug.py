# Generated by Django 2.2.10 on 2020-03-17 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0042_auto_20200128_1045"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="slug",
            field=models.CharField(default=None, max_length=50, unique=True, null=True),
        ),
    ]
