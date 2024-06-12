# Generated by Django 3.2.20 on 2023-07-31 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0083_auto_20230727_0853"),
    ]

    operations = [
        migrations.AddField(
            model_name="personnel",
            name="appraisal_score",
            field=models.IntegerField(blank=True, null=True, verbose_name="appraisal score"),
        ),
        migrations.AddField(
            model_name="personnel",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[
                    ("male", "MALE"),
                    ("female", "FEMALE"),
                    ("agender", "AGENDER"),
                    ("pangender", "PANGENDER"),
                    ("transgender", "TRANSGENDER"),
                    ("third-gender", "THIRD_GENDER"),
                    ("genderqueer", "GENDERQUEER"),
                    ("gender-neutral", "GENDER_NEUTRAL"),
                    ("non-binary", "NON_BINARY"),
                    ("two-spirit", "TWO_SPIRIT"),
                    ("hidden", "HIDDEN"),
                ],
                max_length=15,
                null=True,
                verbose_name="gender",
            ),
        ),
        migrations.AddField(
            model_name="personnel",
            name="location",
            field=models.CharField(max_length=300, null=True, verbose_name="location"),
        ),
    ]
