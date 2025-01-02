# Generated by Django 4.2.16 on 2024-11-20 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0214_alter_profile_limit_access_to_guest"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="title",
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AddField(
            model_name="event",
            name="title_ar",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="event",
            name="title_en",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="event",
            name="title_es",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="event",
            name="title_fr",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="fr_num",
            field=models.IntegerField(blank=True, null=True, verbose_name="field report number"),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="title",
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="title_ar",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="title_en",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="title_es",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="fieldreport",
            name="title_fr",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]