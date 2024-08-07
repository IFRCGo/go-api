# Generated by Django 3.2.20 on 2023-11-03 09:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0185_alter_fieldreport_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fieldreport",
            name="gov_affected_pop_centres",
            field=models.CharField(
                blank=True, max_length=512, null=True, verbose_name="affected population centres (government)"
            ),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="gov_num_affected",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of affected (government)"),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="gov_num_assisted",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of assisted (government)"),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="gov_num_dead",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of dead (government)"),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="gov_num_displaced",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of displaced (government)"),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="gov_num_highest_risk",
            field=models.IntegerField(blank=True, null=True, verbose_name="people at highest risk (government)"),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="gov_num_injured",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of injured (government)"),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="gov_num_missing",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of missing (government)"),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="gov_num_potentially_affected",
            field=models.IntegerField(blank=True, null=True, verbose_name="potentially affected (government)"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsdataset",
            name="livelihoods_and_basic_needs_female",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic needs female"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsdataset",
            name="livelihoods_and_basic_needs_male",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic needs male"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsdataset",
            name="livelihoods_and_basic_needs_people_reached",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic people reached"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsdataset",
            name="livelihoods_and_basic_needs_people_targeted",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic people targeted"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsdataset",
            name="livelihoods_and_basic_needs_requirements",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic needs requirements"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsdataset",
            name="raw_livelihoods_and_basic_needs_female",
            field=models.TextField(blank=True, null=True, verbose_name="number of livelihoods and basic needs female (raw)"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsdataset",
            name="raw_livelihoods_and_basic_needs_male",
            field=models.TextField(blank=True, null=True, verbose_name="number of livelihoods and basic needs male (raw)"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsdataset",
            name="raw_livelihoods_and_basic_needs_people_reached",
            field=models.TextField(
                blank=True, null=True, verbose_name="number of livelihoods and basic needs people reached (raw)"
            ),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsdataset",
            name="raw_livelihoods_and_basic_needs_people_targeted",
            field=models.TextField(
                blank=True, null=True, verbose_name="number of livelihoods and basic needs people targeted (raw)"
            ),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsdataset",
            name="raw_livelihoods_and_basic_needs_requirements",
            field=models.TextField(
                blank=True, null=True, verbose_name="number of livelihoods and basic needs requirements (raw)"
            ),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsea",
            name="livelihoods_and_basic_needs_female",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic needs female"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsea",
            name="livelihoods_and_basic_needs_male",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic needs male"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsea",
            name="livelihoods_and_basic_needs_people_reached",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic people reached"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsea",
            name="livelihoods_and_basic_needs_people_targeted",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic people targeted"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsea",
            name="livelihoods_and_basic_needs_requirements",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic needs requirements"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsea",
            name="raw_livelihoods_and_basic_needs_female",
            field=models.TextField(blank=True, null=True, verbose_name="number of livelihoods and basic needs female (raw)"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsea",
            name="raw_livelihoods_and_basic_needs_male",
            field=models.TextField(blank=True, null=True, verbose_name="number of livelihoods and basic needs male (raw)"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsea",
            name="raw_livelihoods_and_basic_needs_people_reached",
            field=models.TextField(
                blank=True, null=True, verbose_name="number of livelihoods and basic needs people reached (raw)"
            ),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsea",
            name="raw_livelihoods_and_basic_needs_people_targeted",
            field=models.TextField(
                blank=True, null=True, verbose_name="number of livelihoods and basic needs people targeted (raw)"
            ),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsea",
            name="raw_livelihoods_and_basic_needs_requirements",
            field=models.TextField(
                blank=True, null=True, verbose_name="number of livelihoods and basic needs requirements (raw)"
            ),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsfr",
            name="livelihoods_and_basic_needs_female",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic needs female"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsfr",
            name="livelihoods_and_basic_needs_male",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic needs male"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsfr",
            name="livelihoods_and_basic_needs_people_reached",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic people reached"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsfr",
            name="livelihoods_and_basic_needs_requirements",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic needs requirements"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsfr",
            name="raw_livelihoods_and_basic_needs_female",
            field=models.TextField(blank=True, null=True, verbose_name="number of livelihoods and basic needs female (raw)"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsfr",
            name="raw_livelihoods_and_basic_needs_male",
            field=models.TextField(blank=True, null=True, verbose_name="number of livelihoods and basic needs male (raw)"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsfr",
            name="raw_livelihoods_and_basic_needs_people_reached",
            field=models.TextField(
                blank=True, null=True, verbose_name="number of livelihoods and basic needs people reached (raw)"
            ),
        ),
        migrations.AlterField(
            model_name="emergencyoperationsfr",
            name="raw_livelihoods_and_basic_needs_requirements",
            field=models.TextField(
                blank=True, null=True, verbose_name="number of livelihoods and basic needs requirements (raw)"
            ),
        ),
        migrations.AlterField(
            model_name="emergencyoperationspeoplereached",
            name="livelihoods_and_basic_needs_female",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic needs female"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationspeoplereached",
            name="livelihoods_and_basic_needs_male",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic needs male"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationspeoplereached",
            name="livelihoods_and_basic_needs_people_reached",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic people reached"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationspeoplereached",
            name="livelihoods_and_basic_needs_requirements",
            field=models.IntegerField(blank=True, null=True, verbose_name="number of livelihoods and basic needs requirements"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationspeoplereached",
            name="raw_livelihoods_and_basic_needs_female",
            field=models.TextField(blank=True, null=True, verbose_name="number of livelihoods and basic needs female (raw)"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationspeoplereached",
            name="raw_livelihoods_and_basic_needs_male",
            field=models.TextField(blank=True, null=True, verbose_name="number of livelihoods and basic needs male (raw)"),
        ),
        migrations.AlterField(
            model_name="emergencyoperationspeoplereached",
            name="raw_livelihoods_and_basic_needs_people_reached",
            field=models.TextField(
                blank=True, null=True, verbose_name="number of livelihoods and basic needs people reached (raw)"
            ),
        ),
        migrations.AlterField(
            model_name="emergencyoperationspeoplereached",
            name="raw_livelihoods_and_basic_needs_requirements",
            field=models.TextField(
                blank=True, null=True, verbose_name="number of livelihoods and basic needs requirements (raw)"
            ),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="eru_water_sanitation_15",
            field=models.IntegerField(
                choices=[(0, "No"), (1, "Requested"), (2, "Planned"), (3, "Completed")],
                default=0,
                verbose_name="ERU water sanitation M15",
            ),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="eru_water_sanitation_15_units",
            field=models.IntegerField(blank=True, null=True, verbose_name="ERU water sanitation M15 units"),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="eru_water_sanitation_20",
            field=models.IntegerField(
                choices=[(0, "No"), (1, "Requested"), (2, "Planned"), (3, "Completed")],
                default=0,
                verbose_name="ERU water sanitation MSM20",
            ),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="eru_water_sanitation_20_units",
            field=models.IntegerField(blank=True, null=True, verbose_name="ERU water sanitation MSM20 units"),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="eru_water_sanitation_40",
            field=models.IntegerField(
                choices=[(0, "No"), (1, "Requested"), (2, "Planned"), (3, "Completed")],
                default=0,
                verbose_name="ERU water sanitation M40",
            ),
        ),
        migrations.AlterField(
            model_name="fieldreport",
            name="eru_water_sanitation_40_units",
            field=models.IntegerField(blank=True, null=True, verbose_name="ERU water sanitation M40 units"),
        ),
    ]
