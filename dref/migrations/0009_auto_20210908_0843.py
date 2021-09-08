# Generated by Django 2.2.20 on 2021-09-08 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dref', '0008_auto_20210906_0953'),
    ]

    operations = [
        migrations.AlterField(
            model_name='identifiedneed',
            name='title',
            field=models.CharField(choices=[('shelter_and_basic_household_items', 'Shelter And Basic Household Items'), ('livelihoods_and_basic_needs', 'Livelihoods And Basic Needs'), ('health', 'Health'), ('water_sanitation_and_hygiene', 'Water, Sanitation And Hygiene'), ('protection_gender_and_inculsion', 'Protection, Gender And Inculsion'), ('education', 'Education'), ('migration', 'Migration'), ('risk_reduction_climate_adaptation_and_recovery', 'Risk Reduction, Climate Adaptation And Recovery'), ('community_engagement_and _accountability', 'Community Engagement And Accountability'), ('environment_sustainability ', 'Environment Sustainability'), ('shelter_cluster_coordination', 'Shelter Cluster Coordination')], max_length=255, verbose_name='title'),
        ),
    ]
