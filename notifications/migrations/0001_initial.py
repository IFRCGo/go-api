# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-02-07 21:09
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import notifications.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stype", models.IntegerField(default=0, choices=notifications.models.SubscriptionType.choices)),
                ("rtype", models.IntegerField(default=0, choices=notifications.models.RecordType.choices)),
                ("lookup_id", models.CharField(blank=True, editable=False, max_length=20, null=True)),
                (
                    "country",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="api.Country"),
                ),
                (
                    "dtype",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="api.DisasterType"),
                ),
                (
                    "region",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="api.Region"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="subscription", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SurgeAlert",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("atype", models.IntegerField(default=0, choices=notifications.models.SurgeAlertType.choices)),
                ("category", models.IntegerField(default=0, choices=notifications.models.SurgeAlertCategory.choices)),
                ("operation", models.CharField(max_length=100)),
                ("message", models.TextField()),
                ("deployment_needed", models.BooleanField(default=False)),
                ("is_private", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField()),
                ("event", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="api.Event")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
