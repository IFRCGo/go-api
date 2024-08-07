# Generated by Django 2.2.27 on 2022-03-10 05:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployments", "0047_emergencyproject_country"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmergencyProjectActivityLocation",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("latitude", models.IntegerField(verbose_name="latitude")),
                ("longitude", models.IntegerField(verbose_name="longitude")),
                ("description", models.TextField(verbose_name="location description")),
            ],
        ),
        migrations.RemoveField(
            model_name="emergencyprojectactivity",
            name="location_description",
        ),
        migrations.RemoveField(
            model_name="emergencyprojectactivity",
            name="location_point",
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="amount",
            field=models.IntegerField(blank=True, null=True, verbose_name="Amount"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="household_count",
            field=models.IntegerField(blank=True, null=True, verbose_name="Household"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="item_count",
            field=models.IntegerField(blank=True, null=True, verbose_name="Item"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="other_0_5_count",
            field=models.IntegerField(blank=True, null=True, verbose_name="Others/Unknown 0-5"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="other_13_17_count",
            field=models.IntegerField(blank=True, null=True, verbose_name="Others/Unknown 13-17"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="other_18_29_count",
            field=models.IntegerField(blank=True, null=True, verbose_name="Others/Unknown 18-29"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="other_30_39_count",
            field=models.IntegerField(blank=True, null=True, verbose_name="Others/Unknown 30-39"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="other_40_49_count",
            field=models.IntegerField(blank=True, null=True, verbose_name="Others/Unknown 40-49"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="other_50_59_count",
            field=models.IntegerField(blank=True, null=True, verbose_name="Others/Unknown 50-59"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="other_60_69_count",
            field=models.IntegerField(blank=True, null=True, verbose_name="Others/Unknown 60-69"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="other_6_12_count",
            field=models.IntegerField(blank=True, null=True, verbose_name="Others/Unknown 6-12"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="other_70_plus_count",
            field=models.IntegerField(blank=True, null=True, verbose_name="Others/Unknown 70+"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="point_count",
            field=models.IntegerField(blank=True, null=True, verbose_name="Point Count"),
        ),
        migrations.AddField(
            model_name="emergencyprojectactivity",
            name="points",
            field=models.ManyToManyField(blank=True, to="deployments.EmergencyProjectActivityLocation", verbose_name="Points"),
        ),
    ]
