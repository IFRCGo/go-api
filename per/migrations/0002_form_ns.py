# Generated by Django 2.0.12 on 2019-04-15 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("per", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="form",
            name="ns",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
