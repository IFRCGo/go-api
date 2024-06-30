# Generated by Django 4.2.13 on 2024-06-10 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("country_plan", "0006_alter_countryplan_created_by_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="membershipcoordination",
            name="sector",
            field=models.CharField(
                choices=[
                    ("climate", "Climate"),
                    ("crisis", "Crisis"),
                    ("health", "Health"),
                    ("migration", "Migration"),
                    ("inclusion", "Inclusion"),
                    ("enabling_functions", "Enabling functions"),
                ],
                max_length=100,
                verbose_name="Sector",
            ),
        ),
        migrations.AlterField(
            model_name="strategicpriority",
            name="type",
            field=models.CharField(
                choices=[
                    ("ongoing_emergency_operations", "Ongoing emergency operations"),
                    ("climate_and_environment", "Climate and environment"),
                    ("disasters_and_crisis", "Disasters and crisis"),
                    ("health_and_wellbeing", "Health and wellbeing"),
                    ("migration_and_displacement", "Migration and displacement"),
                    ("value_power_and_inclusion", "Values, power and inclusion"),
                ],
                max_length=100,
                verbose_name="Type",
            ),
        ),
    ]