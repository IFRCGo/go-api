# Generated by Django 2.2.13 on 2020-11-04 03:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0033_molnixtag"),
        ("notifications", "0007_auto_20200810_1116"),
    ]

    operations = [
        migrations.AddField(
            model_name="surgealert",
            name="closes",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="surgealert",
            name="end",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="surgealert",
            name="molnix_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="surgealert",
            name="molnix_tags",
            field=models.ManyToManyField(blank=True, to="deployments.MolnixTag"),
        ),
        migrations.AddField(
            model_name="surgealert",
            name="opens",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="surgealert",
            name="start",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
