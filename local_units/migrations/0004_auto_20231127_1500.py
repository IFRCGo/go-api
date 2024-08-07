# Generated by Django 3.2.20 on 2023-11-27 15:00

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("local_units", "0003_alter_localunit_validated"),
    ]

    operations = [
        migrations.CreateModel(
            name="LocalUnitLevel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "level",
                    models.IntegerField(
                        validators=[django.core.validators.MaxValueValidator(10), django.core.validators.MinValueValidator(0)],
                        verbose_name="Level",
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="Name")),
            ],
        ),
        migrations.AddField(
            model_name="localunit",
            name="subtype",
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name="Subtype"),
        ),
        migrations.AlterField(
            model_name="localunittype",
            name="level",
            field=models.IntegerField(
                validators=[django.core.validators.MaxValueValidator(10), django.core.validators.MinValueValidator(0)],
                verbose_name="Type Code",
            ),
        ),
        migrations.AddField(
            model_name="localunit",
            name="level",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="local_unit_level",
                to="local_units.localunitlevel",
                verbose_name="Level",
            ),
        ),
        migrations.AddField(
            model_name="localunit",
            name="is_public",
            field=models.BooleanField(default=False, verbose_name="Is public?"),
        ),
        migrations.AddField(
            model_name="localunit",
            name="date_of_data",
            field=models.DateField(blank=True, null=True, verbose_name="Date of data collection"),
        ),
        migrations.AlterField(
            model_name="localunit",
            name="modified_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Modified at"),
        ),
        migrations.RenameField(
            model_name="localunittype",
            old_name="level",
            new_name="code",
        ),
    ]
