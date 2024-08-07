# Generated by Django 2.2.27 on 2022-07-25 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dref", "0019_auto_20220725_0835"),
    ]

    operations = [
        migrations.CreateModel(
            name="RiskSecurity",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "title",
                    models.CharField(
                        choices=[("risk", "Risk"), ("mitigation_action", "Mitigation Action")],
                        max_length=50,
                        verbose_name="Title",
                    ),
                ),
                ("security_concern", models.TextField(blank=True, null=True, verbose_name="Security Concern")),
            ],
        ),
        migrations.AddField(
            model_name="dref",
            name="risk_security",
            field=models.ManyToManyField(blank=True, to="dref.RiskSecurity", verbose_name="Risk Security"),
        ),
    ]
