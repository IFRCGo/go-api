# Generated by Django 2.2.13 on 2020-07-07 12:31

import django.contrib.gis.db.models.fields
from django.contrib.postgres.operations import CreateExtension
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0074_auto_20200701_0939"),
    ]

    operations = [
        CreateExtension("postgis"),
        migrations.AddField(
            model_name="country",
            name="bbox",
            field=django.contrib.gis.db.models.fields.PolygonField(blank=True, null=True, srid=4326),
        ),
        migrations.AddField(
            model_name="country",
            name="centroid",
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
        migrations.AddField(
            model_name="country",
            name="geom",
            field=django.contrib.gis.db.models.fields.MultiPolygonField(blank=True, null=True, srid=4326),
        ),
    ]
