# Generated by Django 2.2.27 on 2022-08-10 04:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dref", "0025_auto_20220808_0713"),
    ]

    operations = [
        migrations.AlterField(
            model_name="identifiedneed",
            name="title",
            field=models.CharField(
                choices=[
                    ("shelter_housing_and_settlements", "Shelter Housing And Settlements"),
                    ("livelihoods_and_basic_needs", "Livelihoods And Basic Needs"),
                    ("health", "Health"),
                    ("water_sanitation_and_hygiene", "Water, Sanitation And Hygiene"),
                    ("protection_gender_and_inclusion", "Protection, Gender And Inclusion"),
                    ("education", "Education"),
                    ("migration", "Migration"),
                    ("risk_reduction_climate_adaptation_and_recovery", "Risk Reduction, Climate Adaptation And Recovery"),
                    ("community_engagement_and _accountability", "Community Engagement And Accountability"),
                    ("environment_sustainability ", "Environment Sustainability"),
                    ("shelter_cluster_coordination", "Shelter Cluster Coordination"),
                ],
                max_length=255,
                verbose_name="title",
            ),
        ),
        migrations.AlterField(
            model_name="nationalsocietyaction",
            name="title",
            field=models.CharField(
                choices=[
                    ("national_society_readiness", "National Society Readiness"),
                    ("assessment", "Assessment"),
                    ("coordination", "Coordination"),
                    ("resource_mobilization", "Resource Mobilization"),
                    ("activation_of_contingency_plans", "Activation Of Contingency Plans"),
                    ("national_society_eoc", "National Society EOC"),
                    ("shelter_housing and Settlements", "Shelter, Housing and Settlements"),
                    ("livelihoods_and_basic_needs", "Livelihoods And Basic Needs"),
                    ("health", "Health"),
                    ("water_sanitation_and_hygiene", "Water, Sanitation And Hygiene"),
                    ("protection_gender_and_inclusion", "Protection, Gender And Inclusion"),
                    ("education", "Education"),
                    ("migration", "Migration"),
                    ("risk_reduction_climate_adaptation_and_recovery", "Risk Reduction, Climate Adaptation And Recovery"),
                    ("community_engagement_and _accountability", "Community Engagement And Accountability"),
                    ("environment_sustainability ", "Environment Sustainability"),
                    ("multi-purpose_cash", "Multi-purpose Cash"),
                    ("other", "Other"),
                ],
                max_length=255,
                verbose_name="title",
            ),
        ),
    ]
