# Generated by Django 3.2.18 on 2023-04-21 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0077_auto_20230420_1609"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emergencyprojectactivity",
            name="custom_supplies",
            field=models.JSONField(blank=True, default=dict, null=True, verbose_name="custom supplies"),
        ),
        migrations.AlterField(
            model_name="emergencyprojectactivity",
            name="supplies",
            field=models.JSONField(blank=True, default=dict, null=True, verbose_name="supplies"),
        ),
        migrations.AlterField(
            model_name="eru",
            name="type",
            field=models.IntegerField(
                choices=[
                    (0, "Basecamp"),
                    (1, "IT & Telecom"),
                    (2, "Logistics"),
                    (3, "RCRC Emergency Hospital"),
                    (4, "RCRC Emergency Clinic"),
                    (5, "Relief"),
                    (6, "Wash M15"),
                    (7, "Wash MSM20"),
                    (8, "Wash M40"),
                    (9, "Water Supply and rehabilitation"),
                    (10, "Household Water Treatment and safe storage"),
                    (11, "Cholera Case management at Community level"),
                    (12, "Safe and Dignified Burials"),
                    (13, "Community Based Surveillance"),
                    (14, "Base Camp – S"),
                    (15, "Base Camp – M"),
                    (16, "Base Camp – L"),
                    (17, "Outpatient Department (OPD) Module"),
                    (18, "MHPSS"),
                ],
                default=0,
                help_text='<a target="_blank" href="/api/v2/erutype">Key/value pairs</a>',
                verbose_name="type",
            ),
        ),
    ]
