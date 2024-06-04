# Generated by Django 2.2.10 on 2020-04-14 10:21

import re

import django.core.validators
from django.db import migrations, models

import api.utils


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0056_auto_20200413_1010"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="slug",
            field=models.CharField(
                blank=True,
                default=None,
                editable=False,
                help_text="Optional string for a clean URL. For example, go.ifrc.org/emergencies/hurricane-katrina-2019. The string cannot start with a number and is forced to be lowercase. Recommend using hyphens over underscores. Special characters like # is not allowed.",
                max_length=50,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        re.compile("^[-a-zA-Z0-9_]+\\Z"),
                        "Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens.",
                        "invalid",
                    ),
                    api.utils.validate_slug_number,
                ],
            ),
        ),
    ]
