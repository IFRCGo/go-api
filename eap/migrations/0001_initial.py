# Generated by Django 2.2.28 on 2022-07-08 05:56

import deployments.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import eap.models
import enumfields.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0156_appealfilter_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='EAP',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('eap_number', models.CharField(max_length=50, verbose_name='EAP Number')),
                ('approval_date', models.DateField(verbose_name='Date of EAP Approval')),
                ('status', models.CharField(choices=[('approved', 'Approved'), ('activated', 'Activated')], default=eap.models.EAP.Status('activated'), max_length=255, verbose_name='EAP Status')),
                ('operational_timeframe', models.IntegerField(verbose_name='Operational Timeframe (Months)')),
                ('lead_time', models.IntegerField(verbose_name='Lead Time')),
                ('eap_timeframe', models.IntegerField(verbose_name='EAP Timeframe (Years)')),
                ('num_of_people', models.IntegerField(verbose_name='Number of People Targeted')),
                ('total_budget', models.IntegerField(verbose_name='Total Budget (CHF)')),
                ('readiness_budget', models.IntegerField(blank=True, null=True, verbose_name='Readiness Budget (CHF)')),
                ('pre_positioning_budget', models.IntegerField(blank=True, null=True, verbose_name='Pre-positioning Budget (CHF)')),
                ('early_action_budget', models.IntegerField(blank=True, null=True, verbose_name='Early Actions Budget (CHF)')),
                ('trigger_statement', models.TextField(verbose_name='Trigger Statement (Threshold for Activation)')),
                ('overview', models.TextField(verbose_name='EAP Overview')),
                ('document', models.FileField(blank=True, null=True, upload_to='eap/documents/', verbose_name='EAP Documents')),
                ('originator_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Originator Name')),
                ('originator_title', models.CharField(blank=True, max_length=255, null=True, verbose_name='Originator Title')),
                ('originator_email', models.CharField(blank=True, max_length=255, null=True, verbose_name='Originator Email')),
                ('originator_phone', models.CharField(blank=True, max_length=255, null=True, verbose_name='Origingator Phone')),
                ('nsc_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='National Society Contact Name')),
                ('nsc_title', models.CharField(blank=True, max_length=255, null=True, verbose_name='National Society Contact Title')),
                ('nsc_email', models.CharField(blank=True, max_length=255, null=True, verbose_name='National Society Contact Email')),
                ('nsc_phone', models.CharField(blank=True, max_length=255, null=True, verbose_name='National Society Contact Phone')),
                ('ifrc_focal_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Ifrc Focal Point Name')),
                ('ifrc_focal_title', models.CharField(blank=True, max_length=255, null=True, verbose_name='Ifrc Focal Point Title')),
                ('ifrc_focal_email', models.CharField(blank=True, max_length=255, null=True, verbose_name='Ifrc Focal Point Email')),
                ('ifrc_focal_phone', models.CharField(blank=True, max_length=255, null=True, verbose_name='Ifrc Focal Point Phone')),
                ('country', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='eap_country', to='api.Country', verbose_name='Country')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='eap_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Created by')),
                ('disaster_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='eap_disaster_type', to='api.DisasterType', verbose_name='Disaster Type')),
                ('district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='eap_district', to='api.District', verbose_name='Provience/Region')),
            ],
            options={
                'verbose_name': 'Early Action Protocol',
                'verbose_name_plural': 'Early Actions Protocols',
            },
        ),
        migrations.CreateModel(
            name='EarlyActionIndicator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('indicator', models.CharField(blank=True, default=eap.models.EarlyActionIndicator.IndicatorChoices('indicator_1'), max_length=255, null=True, verbose_name=[('indicator_1', 'Indicator 1'), ('indicator_2', 'Indicator 2')])),
                ('indicator_value', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Early Action Indicator',
                'verbose_name_plural': 'Early Actions Indicators',
            },
        ),
        migrations.CreateModel(
            name='EarlyAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sector', models.IntegerField(choices=[(0, 'Shelter, Housing And Settlements'), (1, 'Livelihoods'), (2, 'Multi-purpose Cash'), (3, 'Health And Care'), (4, 'Water, Sanitation And Hygiene'), (5, 'Protection, Gender And Inclusion'), (6, 'Education'), (7, 'Migration'), (8, 'Risk Reduction, Climate Adaptation And Recovery'), (9, 'Community Engagement And Accountability'), (10, 'Environment Sustainability'), (11, 'Shelter Cluster Coordination')], verbose_name='sector')),
                ('budget_per_sector', models.IntegerField(blank=True, null=True, verbose_name='Budget per sector (CHF)')),
                ('prioritized_risk', models.TextField(blank=True, null=True, verbose_name='Prioritized risk')),
                ('targeted_people', models.IntegerField(blank=True, null=True, verbose_name='Targeted people')),
                ('readiness_activities', models.TextField(blank=True, null=True, verbose_name='Readiness Activities')),
                ('prepositioning_activities', models.TextField(blank=True, null=True, verbose_name='Pre-positioning Activities')),
                ('indicators', models.ManyToManyField(blank=True, to='eap.EarlyActionIndicator', verbose_name='Indicators')),
            ],
            options={
                'verbose_name': 'Early Action',
                'verbose_name_plural': 'Early Actions',
            },
        ),
        migrations.CreateModel(
            name='EAPRefrence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(blank=True, max_length=255, null=True, verbose_name='Name')),
                ('url', models.URLField(blank=True, null=True, verbose_name='URL')),
                ('eap', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eap_reference', to='eap.EAP', verbose_name='EAP')),
            ],
            options={
                'verbose_name': 'EAP Refrence',
                'verbose_name_plural': 'EAP Refrences',
            },
        ),
        migrations.CreateModel(
            name='EAPPartner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Name')),
                ('url', models.URLField(blank=True, null=True, verbose_name='URL')),
                ('eap', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eap_partner', to='eap.EAP', verbose_name='EAP')),
            ],
            options={
                'verbose_name': 'EAP Partner',
                'verbose_name_plural': 'EAP Partners',
            },
        ),
        migrations.AddField(
            model_name='eap',
            name='early_actions',
            field=models.ManyToManyField(blank=True, to='eap.EarlyAction', verbose_name='Early actions'),
        ),
        migrations.AddField(
            model_name='eap',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='eap_modified_by', to=settings.AUTH_USER_MODEL, verbose_name='Modified by'),
        ),
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('early_act', models.TextField(blank=True, null=True, verbose_name='Early Actions')),
                ('early_action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action', to='eap.EarlyAction', verbose_name='Early Actions')),
            ],
            options={
                'verbose_name': 'Action',
                'verbose_name_plural': 'Actions',
            },
        ),
    ]