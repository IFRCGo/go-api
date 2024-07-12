# Generated by Django 4.2.13 on 2024-07-09 09:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0089_alter_emergencyproject_districts"),
        ("per", "0120_alter_formcomponent_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="OpsLearningCacheResponse",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("used_filters_hash", models.CharField(max_length=32, verbose_name="used filters hash")),
                ("used_filters", models.JSONField(default=dict, verbose_name="used filters")),
                ("used_prompt_hash", models.CharField(max_length=32, verbose_name="used prompt hash")),
                ("used_prompt", models.TextField(blank=True, null=True, verbose_name="used prompt")),
                ("insights_1", models.TextField(blank=True, null=True, verbose_name="insights 1")),
                ("insights_2", models.TextField(blank=True, null=True, verbose_name="insights 2")),
                ("insights_3", models.TextField(blank=True, null=True, verbose_name="insights 3")),
                ("modified_at", models.DateTimeField(auto_now=True, verbose_name="modified_at")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("used_ops_learning", models.ManyToManyField(related_name="+", to="per.opslearning")),
            ],
        ),
        migrations.CreateModel(
            name="OpsLearningSectorCacheResponse",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("summary", models.TextField(verbose_name="summary")),
                ("modified_at", models.DateTimeField(auto_now=True, verbose_name="modified_at")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                (
                    "filter_response",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ops_learning_sector",
                        to="per.opslearningcacheresponse",
                        verbose_name="filter response",
                    ),
                ),
                (
                    "sector",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="deployments.sectortag",
                        verbose_name="sector",
                    ),
                ),
                ("used_ops_learning", models.ManyToManyField(related_name="+", to="per.opslearning")),
            ],
        ),
        migrations.CreateModel(
            name="OpsLearningComponentCacheResponse",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("summary", models.TextField(verbose_name="summary")),
                ("modified_at", models.DateTimeField(auto_now=True, verbose_name="modified_at")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                (
                    "component",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="per.formcomponent",
                        verbose_name="component",
                    ),
                ),
                (
                    "filter_response",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ops_learning_component",
                        to="per.opslearningcacheresponse",
                        verbose_name="filter response",
                    ),
                ),
                ("used_ops_learning", models.ManyToManyField(related_name="+", to="per.opslearning")),
            ],
        ),
    ]
