# Generated by Django 4.2.16 on 2024-10-18 05:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0089_alter_emergencyproject_districts"),
        ("per", "0121_formcomponent_climate_environmental_considerations_guidance_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="OpsLearningCacheResponse",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("used_filters_hash", models.CharField(max_length=32, verbose_name="used filters hash")),
                ("used_filters", models.JSONField(default=dict, verbose_name="used filters")),
                (
                    "status",
                    models.IntegerField(
                        choices=[(1, "Pending"), (2, "Started"), (3, "Success"), (4, "No extract available"), (5, "Failed")],
                        default=1,
                        verbose_name="status",
                    ),
                ),
                ("insights1_content", models.TextField(blank=True, null=True, verbose_name="insights 1")),
                ("insights1_content_en", models.TextField(blank=True, null=True, verbose_name="insights 1")),
                ("insights1_content_es", models.TextField(blank=True, null=True, verbose_name="insights 1")),
                ("insights1_content_fr", models.TextField(blank=True, null=True, verbose_name="insights 1")),
                ("insights1_content_ar", models.TextField(blank=True, null=True, verbose_name="insights 1")),
                ("insights2_content", models.TextField(blank=True, null=True, verbose_name="insights 2")),
                ("insights2_content_en", models.TextField(blank=True, null=True, verbose_name="insights 2")),
                ("insights2_content_es", models.TextField(blank=True, null=True, verbose_name="insights 2")),
                ("insights2_content_fr", models.TextField(blank=True, null=True, verbose_name="insights 2")),
                ("insights2_content_ar", models.TextField(blank=True, null=True, verbose_name="insights 2")),
                ("insights3_content", models.TextField(blank=True, null=True, verbose_name="insights 3")),
                ("insights3_content_en", models.TextField(blank=True, null=True, verbose_name="insights 3")),
                ("insights3_content_es", models.TextField(blank=True, null=True, verbose_name="insights 3")),
                ("insights3_content_fr", models.TextField(blank=True, null=True, verbose_name="insights 3")),
                ("insights3_content_ar", models.TextField(blank=True, null=True, verbose_name="insights 3")),
                ("insights1_title", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 1 title")),
                ("insights1_title_en", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 1 title")),
                ("insights1_title_es", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 1 title")),
                ("insights1_title_fr", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 1 title")),
                ("insights1_title_ar", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 1 title")),
                ("insights2_title", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 2 title")),
                ("insights2_title_en", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 2 title")),
                ("insights2_title_es", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 2 title")),
                ("insights2_title_fr", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 2 title")),
                ("insights2_title_ar", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 2 title")),
                ("insights3_title", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 3 title")),
                ("insights3_title_en", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 3 title")),
                ("insights3_title_es", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 3 title")),
                ("insights3_title_fr", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 3 title")),
                ("insights3_title_ar", models.CharField(blank=True, max_length=255, null=True, verbose_name="insights 3 title")),
                (
                    "insights1_confidence_level",
                    models.CharField(blank=True, max_length=10, null=True, verbose_name="insights 1 confidence level"),
                ),
                (
                    "insights2_confidence_level",
                    models.CharField(blank=True, max_length=10, null=True, verbose_name="insights 2 confidence level"),
                ),
                (
                    "insights3_confidence_level",
                    models.CharField(blank=True, max_length=10, null=True, verbose_name="insights 3 confidence level"),
                ),
                ("contradictory_reports", models.TextField(blank=True, null=True, verbose_name="contradictory reports")),
                ("modified_at", models.DateTimeField(auto_now=True, verbose_name="modified_at")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                (
                    "export_status",
                    models.IntegerField(
                        choices=[(1, "Pending"), (2, "Success"), (3, "Failed")], default=1, verbose_name="export status"
                    ),
                ),
                (
                    "exported_file",
                    models.FileField(
                        blank=True, null=True, upload_to="ops-learning/summary/export/", verbose_name="exported file"
                    ),
                ),
                ("exported_at", models.DateTimeField(blank=True, null=True, verbose_name="exported at")),
                (
                    "translation_module_original_language",
                    models.CharField(
                        choices=[("en", "English"), ("es", "Spanish"), ("fr", "French"), ("ar", "Arabic")],
                        default="en",
                        help_text="Language used to create this entity",
                        max_length=2,
                        verbose_name="Entity Original language",
                    ),
                ),
                (
                    "translation_module_skip_auto_translation",
                    models.BooleanField(
                        default=False,
                        help_text="Skip auto translation operation for this entity?",
                        verbose_name="Skip auto translation",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="OpsLearningPromptResponseCache",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("prompt_hash", models.CharField(max_length=32, verbose_name="used prompt hash")),
                ("prompt", models.TextField(blank=True, null=True, verbose_name="used prompt")),
                ("type", models.IntegerField(choices=[(1, "Primary"), (2, "Secondary")], verbose_name="type")),
                ("response", models.JSONField(default=dict, verbose_name="response")),
            ],
        ),
        migrations.AddField(
            model_name="opslearning",
            name="learning_ar",
            field=models.TextField(blank=True, null=True, verbose_name="learning"),
        ),
        migrations.AddField(
            model_name="opslearning",
            name="learning_en",
            field=models.TextField(blank=True, null=True, verbose_name="learning"),
        ),
        migrations.AddField(
            model_name="opslearning",
            name="learning_es",
            field=models.TextField(blank=True, null=True, verbose_name="learning"),
        ),
        migrations.AddField(
            model_name="opslearning",
            name="learning_fr",
            field=models.TextField(blank=True, null=True, verbose_name="learning"),
        ),
        migrations.AddField(
            model_name="opslearning",
            name="learning_validated_ar",
            field=models.TextField(blank=True, null=True, verbose_name="learning (validated)"),
        ),
        migrations.AddField(
            model_name="opslearning",
            name="learning_validated_en",
            field=models.TextField(blank=True, null=True, verbose_name="learning (validated)"),
        ),
        migrations.AddField(
            model_name="opslearning",
            name="learning_validated_es",
            field=models.TextField(blank=True, null=True, verbose_name="learning (validated)"),
        ),
        migrations.AddField(
            model_name="opslearning",
            name="learning_validated_fr",
            field=models.TextField(blank=True, null=True, verbose_name="learning (validated)"),
        ),
        migrations.AddField(
            model_name="opslearning",
            name="translation_module_original_language",
            field=models.CharField(
                choices=[("en", "English"), ("es", "Spanish"), ("fr", "French"), ("ar", "Arabic")],
                default="en",
                help_text="Language used to create this entity",
                max_length=2,
                verbose_name="Entity Original language",
            ),
        ),
        migrations.AddField(
            model_name="opslearning",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.CreateModel(
            name="OpsLearningSectorCacheResponse",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField(blank=True, null=True, verbose_name="content")),
                ("content_en", models.TextField(blank=True, null=True, verbose_name="content")),
                ("content_es", models.TextField(blank=True, null=True, verbose_name="content")),
                ("content_fr", models.TextField(blank=True, null=True, verbose_name="content")),
                ("content_ar", models.TextField(blank=True, null=True, verbose_name="content")),
                (
                    "translation_module_original_language",
                    models.CharField(
                        choices=[("en", "English"), ("es", "Spanish"), ("fr", "French"), ("ar", "Arabic")],
                        default="en",
                        help_text="Language used to create this entity",
                        max_length=2,
                        verbose_name="Entity Original language",
                    ),
                ),
                (
                    "translation_module_skip_auto_translation",
                    models.BooleanField(
                        default=False,
                        help_text="Skip auto translation operation for this entity?",
                        verbose_name="Skip auto translation",
                    ),
                ),
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
                ("content", models.TextField(blank=True, null=True, verbose_name="content")),
                ("content_en", models.TextField(blank=True, null=True, verbose_name="content")),
                ("content_es", models.TextField(blank=True, null=True, verbose_name="content")),
                ("content_fr", models.TextField(blank=True, null=True, verbose_name="content")),
                ("content_ar", models.TextField(blank=True, null=True, verbose_name="content")),
                (
                    "translation_module_original_language",
                    models.CharField(
                        choices=[("en", "English"), ("es", "Spanish"), ("fr", "French"), ("ar", "Arabic")],
                        default="en",
                        help_text="Language used to create this entity",
                        max_length=2,
                        verbose_name="Entity Original language",
                    ),
                ),
                (
                    "translation_module_skip_auto_translation",
                    models.BooleanField(
                        default=False,
                        help_text="Skip auto translation operation for this entity?",
                        verbose_name="Skip auto translation",
                    ),
                ),
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
        migrations.AddField(
            model_name="opslearningcacheresponse",
            name="used_ops_learning",
            field=models.ManyToManyField(related_name="+", to="per.opslearning"),
        ),
    ]
