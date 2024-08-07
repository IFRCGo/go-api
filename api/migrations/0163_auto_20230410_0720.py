# Generated by Django 3.2.18 on 2023-04-10 07:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0162_admin2_created_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="action",
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
            model_name="action",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="actionstaken",
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
            model_name="actionstaken",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="appeal",
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
            model_name="appeal",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="appealdocument",
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
            model_name="appealdocument",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="country",
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
            model_name="country",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="countrysnippet",
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
            model_name="countrysnippet",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="disastertype",
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
            model_name="disastertype",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="event",
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
            model_name="event",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="eventfeatureddocument",
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
            model_name="eventfeatureddocument",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="eventlink",
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
            model_name="eventlink",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="externalpartner",
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
            model_name="externalpartner",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="fieldreport",
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
            model_name="fieldreport",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="gdacsevent",
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
            model_name="gdacsevent",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="generaldocument",
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
            model_name="generaldocument",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="maincontact",
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
            model_name="maincontact",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="region",
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
            model_name="region",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="regionemergencysnippet",
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
            model_name="regionemergencysnippet",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="regionpreparednesssnippet",
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
            model_name="regionpreparednesssnippet",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="regionprofilesnippet",
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
            model_name="regionprofilesnippet",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="regionsnippet",
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
            model_name="regionsnippet",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="situationreport",
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
            model_name="situationreport",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="situationreporttype",
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
            model_name="situationreporttype",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="snippet",
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
            model_name="snippet",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
        migrations.AddField(
            model_name="supportedactivity",
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
            model_name="supportedactivity",
            name="translation_module_skip_auto_translation",
            field=models.BooleanField(
                default=False, help_text="Skip auto translation operation for this entity?", verbose_name="Skip auto translation"
            ),
        ),
    ]
