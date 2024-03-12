# Generated by Django 3.2.23 on 2024-03-12 04:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dref', '0076_auto_20240306_0603'),
    ]

    operations = [
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='any_other_actor',
            field=models.TextField(blank=True, help_text='Has any other actor in the country activated an early action protocol?', null=True, verbose_name='Actor in country activated early action protocol?'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='ifrc_anticipatory_email',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ifrc focal point for anticipatory email'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='ifrc_anticipatory_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ifrc focal point for anticipatory name'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='ifrc_anticipatory_phone_number',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='ifrc focal point for anticipatory phone number'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='ifrc_anticipatory_title',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ifrc focal point for anticipatory title'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='immediate_boys',
            field=models.IntegerField(blank=True, help_text='Boys under 18', null=True, verbose_name='boys'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='immediate_disability_people_per',
            field=models.FloatField(blank=True, help_text='Estimated % people disability for immediate response', null=True, verbose_name='disability people for immediate response'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='immediate_displaced_people',
            field=models.IntegerField(blank=True, help_text='Estimated number of displaced people for immediate response', null=True, verbose_name='displaced people for immediate response'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='immediate_girls',
            field=models.IntegerField(blank=True, help_text='Girls under 18', null=True, verbose_name='girls'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='immediate_men',
            field=models.IntegerField(blank=True, null=True, verbose_name='men'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='immediate_people_per_local',
            field=models.FloatField(blank=True, help_text='Estimated % people Rural for immediate response', null=True, verbose_name='people per local for immediate response'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='immediate_people_per_urban',
            field=models.FloatField(blank=True, help_text='Estimated % people Urban for immediate response', null=True, verbose_name='people per urban for immediate response'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='immediate_total_targeted_population',
            field=models.IntegerField(blank=True, help_text='Estimated number of targeted people', null=True, verbose_name='total targeted population for immediate response'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='immediate_women',
            field=models.IntegerField(blank=True, null=True, verbose_name='women'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='lead_time_for_early_action',
            field=models.TextField(blank=True, null=True, verbose_name='lead time for early action'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='ns_disaster_risk_reduction',
            field=models.TextField(blank=True, help_text='Has the National Society implemented relevant Disaster Risk Reduction activities in the same geographical area that this plan builds upon?', null=True, verbose_name='Has the National Society implemented disaster Risk Reduction activities?'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='ns_eaps',
            field=models.TextField(blank=True, help_text='Does the National Society have EAPs or simplified EAPs active, triggered or under development?', null=True, verbose_name='Does the NS have EAPS?'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='ns_mandate',
            field=models.TextField(blank=True, help_text='Does the National Society have the mandate to act before the impact of the hazard?', null=True, verbose_name='Does the NS have the mandate?'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='ns_mitigating_measures',
            field=models.TextField(blank=True, help_text='Is the National Society implementing other mitigating measures through other sources of funds', null=True, verbose_name='Does the NS have mitigating measures?'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='other_actor_file',
            field=models.ManyToManyField(blank=True, related_name='dref_operational_update_other_actor_file', to='dref.DrefFile', verbose_name='Other Actor file'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='selection_criteria_expected_impacted_population',
            field=models.TextField(blank=True, help_text='For the expected impacted population if the hazard materialises for the immediate response activities', null=True, verbose_name='selection criteria for expected impacted population'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='targeting_expected_impacted_population',
            field=models.TextField(blank=True, help_text='Targeting of the expected impacted population if the disaster materialises for the immediate response activities.', null=True, verbose_name='targeting expected impacted population'),
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='threshold_for_early_action',
            field=models.TextField(blank=True, null=True, verbose_name='threshold for early action'),
        ),
    ]
