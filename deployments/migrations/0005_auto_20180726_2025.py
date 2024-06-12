# Generated by Django 2.0.5 on 2018-07-26 20:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0009_auto_20180712_1922"),
        ("deployments", "0004_auto_20180621_1519"),
    ]

    operations = [
        migrations.CreateModel(
            name="Personnel",
            fields=[
                (
                    "deployedperson_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="deployments.DeployedPerson",
                    ),
                ),
                ("type", models.CharField(choices=[("fact", "FACT"), ("heop", "HEOP"), ("rdrt", "RDRT")], max_length=4)),
                (
                    "country_from",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="personnel_deployments",
                        to="api.Country",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Personnel",
            },
            bases=("deployments.deployedperson",),
        ),
        migrations.CreateModel(
            name="PersonnelDeployment",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("comments", models.TextField(blank=True, null=True)),
                ("country_deployed_to", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="api.Country")),
                (
                    "event_deployed_to",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="api.Event"),
                ),
                ("region_deployed_to", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="api.Region")),
            ],
            options={
                "verbose_name_plural": "Personnel Deployments",
            },
        ),
        migrations.AddField(
            model_name="personnel",
            name="deployment",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="deployments.PersonnelDeployment"),
        ),
    ]
