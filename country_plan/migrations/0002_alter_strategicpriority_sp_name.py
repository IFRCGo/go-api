# Generated by Django 3.2.16 on 2022-11-23 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('country_plan', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='strategicpriority',
            name='sp_name',
            field=models.CharField(blank=True, choices=[('climate_and_environmental_crisis', 'Climate and environmental crisis'), ('evolving_crisis_and_disasters', 'Evolving crisis and disasters'), ('growing_gaps_in_health_and_wellbeing', 'Growing gaps in health and wellbeing'), ('migration_and_identity', 'Migration and Identity'), ('value_power_and_inclusion', 'Value power and inclusion')], max_length=100, null=True, verbose_name='Strategic Priority'),
        ),
    ]
