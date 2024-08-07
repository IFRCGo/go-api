# Generated by Django 2.0.12 on 2019-07-24 08:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0022_appeal_real_data_update"),
    ]

    operations = [
        migrations.AddField(
            model_name="fieldreport",
            name="other_num_affected",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="other_num_assisted",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="other_num_dead",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="other_num_displaced",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="other_num_injured",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="other_num_missing",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="start_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
