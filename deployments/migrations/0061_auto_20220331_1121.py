# Generated by Django 2.2.27 on 2022-03-31 11:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0060_auto_20220323_1527"),
    ]

    operations = [
        migrations.RenameField(
            model_name="emergencyprojectactivity",
            old_name="disabled_femal_0_1",
            new_name="disabled_female_0_1_count",
        ),
        migrations.RenameField(
            model_name="emergencyprojectactivity",
            old_name="disabled_male_0_1",
            new_name="disabled_male_0_1_count",
        ),
        migrations.RenameField(
            model_name="emergencyprojectactivity",
            old_name="disabled_other_0_1",
            new_name="disabled_other_0_1_count",
        ),
        migrations.RenameField(
            model_name="emergencyprojectactivity",
            old_name="female_0_1",
            new_name="female_0_1_count",
        ),
        migrations.RenameField(
            model_name="emergencyprojectactivity",
            old_name="male_0_1",
            new_name="male_0_1_count",
        ),
        migrations.RenameField(
            model_name="emergencyprojectactivity",
            old_name="other_0_1",
            new_name="other_0_1_count",
        ),
    ]
