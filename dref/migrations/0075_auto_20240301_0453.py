# Generated by Django 3.2.23 on 2024-03-01 04:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dref', '0074_auto_20240129_0909'),
    ]

    operations = [
        migrations.AddField(
            model_name='dref',
            name='any_other_actor',
            field=models.TextField(blank=True, help_text='Has any other actor in the country activated an early action protocol?', null=True, verbose_name='Actor in country activated early action protocol?'),
        ),
        migrations.AddField(
            model_name='dref',
            name='ifrc_anticipatory_email',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ifrc focal point for anticipatory email'),
        ),
        migrations.AddField(
            model_name='dref',
            name='ifrc_anticipatory_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ifrc focal point for anticipatory name'),
        ),
        migrations.AddField(
            model_name='dref',
            name='ifrc_anticipatory_phone_number',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='ifrc focal point for anticipatory phone number'),
        ),
        migrations.AddField(
            model_name='dref',
            name='ifrc_anticipatory_title',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ifrc focal point for anticipatory title'),
        ),
        migrations.AddField(
            model_name='dref',
            name='immediate_boys',
            field=models.IntegerField(blank=True, help_text='Boys under 18', null=True, verbose_name='boys'),
        ),
        migrations.AddField(
            model_name='dref',
            name='immediate_disability_people_per',
            field=models.FloatField(blank=True, help_text='Estimated % people disability for immediate response', null=True, verbose_name='disability people for immediate response'),
        ),
        migrations.AddField(
            model_name='dref',
            name='immediate_displaced_people',
            field=models.IntegerField(blank=True, help_text='Estimated number of displaced people for immediate response', null=True, verbose_name='displaced people for immediate response'),
        ),
        migrations.AddField(
            model_name='dref',
            name='immediate_girls',
            field=models.IntegerField(blank=True, help_text='Girls under 18', null=True, verbose_name='girls'),
        ),
        migrations.AddField(
            model_name='dref',
            name='immediate_men',
            field=models.IntegerField(blank=True, null=True, verbose_name='men'),
        ),
        migrations.AddField(
            model_name='dref',
            name='immediate_people_per_local',
            field=models.FloatField(blank=True, help_text='Estimated % people Rural for immediate response', null=True, verbose_name='people per local for immediate response'),
        ),
        migrations.AddField(
            model_name='dref',
            name='immediate_people_per_urban',
            field=models.FloatField(blank=True, help_text='Estimated % people Urban for immediate response', null=True, verbose_name='people per urban for immediate response'),
        ),
        migrations.AddField(
            model_name='dref',
            name='immediate_total_targeted_population',
            field=models.IntegerField(blank=True, help_text='Estimated number of targeted people', null=True, verbose_name='total targeted population for immediate response'),
        ),
        migrations.AddField(
            model_name='dref',
            name='immediate_women',
            field=models.IntegerField(blank=True, null=True, verbose_name='women'),
        ),
        migrations.AddField(
            model_name='dref',
            name='lead_time_for_early_action',
            field=models.TextField(blank=True, null=True, verbose_name='lead time for early action'),
        ),
        migrations.AddField(
            model_name='dref',
            name='ns_disaster_risk_reduction',
            field=models.TextField(blank=True, help_text='Has the National Society implemented relevant Disaster Risk Reduction activities in the same geographical area that this plan builds upon?', null=True, verbose_name='Has the National Society implemented disaster Risk Reduction activities?'),
        ),
        migrations.AddField(
            model_name='dref',
            name='ns_eaps',
            field=models.TextField(blank=True, help_text='Does the National Society have EAPs or simplified EAPs active, triggered or under development?', null=True, verbose_name='Does the NS have EAPS?'),
        ),
        migrations.AddField(
            model_name='dref',
            name='ns_mandate',
            field=models.TextField(blank=True, help_text='Does the National Society have the mandate to act before the impact of the hazard?', null=True, verbose_name='Does the NS have the mandate?'),
        ),
        migrations.AddField(
            model_name='dref',
            name='ns_mitigating_measures',
            field=models.TextField(blank=True, help_text='Is the National Society implementing other mitigating measures through other sources of funds', null=True, verbose_name='Does the NS have mitigating measures?'),
        ),
        migrations.AddField(
            model_name='dref',
            name='other_actor_file',
            field=models.ManyToManyField(blank=True, related_name='dref_other_actor_file', to='dref.DrefFile', verbose_name='Other Actor file'),
        ),
        migrations.AddField(
            model_name='dref',
            name='selection_criteria_early_action',
            field=models.TextField(blank=True, help_text='For population at risk for the early actions', null=True, verbose_name='selection criteria for early action'),
        ),
        migrations.AddField(
            model_name='dref',
            name='selection_criteria_expected_impacted_population',
            field=models.TextField(blank=True, help_text='For the expected impacted population if the hazard materialises for the immediate response activities', null=True, verbose_name='selection criteria for expected impacted population'),
        ),
        migrations.AddField(
            model_name='dref',
            name='targeting_expected_impacted_population',
            field=models.TextField(blank=True, help_text='Targeting of the expected impacted population if the disaster materialises for the immediate response activities.', null=True, verbose_name='targeting expected impacted population'),
        ),
        migrations.AddField(
            model_name='dref',
            name='targeting_population_early_action',
            field=models.TextField(blank=True, null=True, verbose_name='Targeting of population at risk for the early actions'),
        ),
        migrations.AddField(
            model_name='dref',
            name='threshold_for_early_action',
            field=models.TextField(blank=True, null=True, verbose_name='threshold for early action'),
        ),
        migrations.AddField(
            model_name='identifiedneed',
            name='current_need',
            field=models.TextField(blank=True, null=True, verbose_name='current need'),
        ),
        migrations.AddField(
            model_name='identifiedneed',
            name='expected_need',
            field=models.TextField(blank=True, null=True, verbose_name='expected need'),
        ),
        migrations.AddField(
            model_name='plannedintervention',
            name='early_action_block',
            field=models.TextField(blank=True, null=True, verbose_name='early action block'),
        ),
        migrations.AddField(
            model_name='plannedintervention',
            name='early_response_block',
            field=models.TextField(blank=True, null=True, verbose_name='early response block'),
        ),
        migrations.AddField(
            model_name='plannedintervention',
            name='people_targeted_by_early_action',
            field=models.IntegerField(blank=True, null=True, verbose_name='people targeted by early action'),
        ),
        migrations.AddField(
            model_name='plannedintervention',
            name='people_targeted_by_immediate_response',
            field=models.IntegerField(blank=True, null=True, verbose_name='people targeted by immediate response'),
        ),
        migrations.AddField(
            model_name='plannedintervention',
            name='readiness_block',
            field=models.TextField(blank=True, null=True, verbose_name='readiness block'),
        ),
    ]
