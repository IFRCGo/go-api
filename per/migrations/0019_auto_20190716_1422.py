# Generated by Django 2.0.12 on 2019-07-16 14:22

from django.db import migrations, models

import per.models


class Migration(migrations.Migration):

    dependencies = [
        ("per", "0018_draft_country"),
    ]

    operations = [
        migrations.AddField(
            model_name="overview",
            name="date_of_last_capacity_assessment",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="overview",
            name="type_of_last_capacity_assessment",
            field=models.IntegerField(default=0, choices=per.models.CAssessmentType.choices),
        ),
    ]
