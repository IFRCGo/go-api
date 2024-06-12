# Generated by Django 2.0.12 on 2019-07-11 08:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0009_auto_20190708_1626"),
    ]

    operations = [
        migrations.AlterField(
            model_name="eru",
            name="alert_date",
            field=models.DateTimeField(help_text="Still not used in frontend", null=True),
        ),
        migrations.AlterField(
            model_name="eru",
            name="appeal",
            field=models.ForeignKey(
                blank=True,
                help_text="Still not used in frontend",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="api.Appeal",
            ),
        ),
        migrations.AlterField(
            model_name="eru",
            name="end_date",
            field=models.DateTimeField(help_text="Still not used in frontend", null=True),
        ),
        migrations.AlterField(
            model_name="eru",
            name="num_people_deployed",
            field=models.IntegerField(default=0, help_text="Still not used in frontend"),
        ),
        migrations.AlterField(
            model_name="eru",
            name="start_date",
            field=models.DateTimeField(help_text="Still not used in frontend", null=True),
        ),
        migrations.AlterField(
            model_name="eru",
            name="supporting_societies",
            field=models.CharField(blank=True, help_text="Still not used in frontend", max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name="personneldeployment",
            name="alert_date",
            field=models.DateTimeField(help_text="Still not used in frontend", null=True),
        ),
        migrations.AlterField(
            model_name="personneldeployment",
            name="appeal_deployed_to",
            field=models.ForeignKey(
                blank=True,
                help_text="Still not used in frontend",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="api.Appeal",
            ),
        ),
        migrations.AlterField(
            model_name="personneldeployment",
            name="end_date",
            field=models.DateTimeField(help_text="Still not used in frontend", null=True),
        ),
        migrations.AlterField(
            model_name="personneldeployment",
            name="end_duration",
            field=models.CharField(blank=True, help_text="Still not used in frontend", max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="personneldeployment",
            name="exp_start_date",
            field=models.DateTimeField(help_text="Still not used in frontend", null=True),
        ),
        migrations.AlterField(
            model_name="personneldeployment",
            name="start_date",
            field=models.DateTimeField(help_text="Still not used in frontend", null=True),
        ),
    ]
