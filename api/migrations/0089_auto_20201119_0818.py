# Generated by Django 2.2.13 on 2020-11-19 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0088_auto_20201119_0809"),
    ]

    operations = [
        migrations.AddField(
            model_name="regionemergencysnippet",
            name="title_ar",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="regionemergencysnippet",
            name="title_en",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="regionemergencysnippet",
            name="title_es",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="regionemergencysnippet",
            name="title_fr",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="regionpreparednesssnippet",
            name="title_ar",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="regionpreparednesssnippet",
            name="title_en",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="regionpreparednesssnippet",
            name="title_es",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="regionpreparednesssnippet",
            name="title_fr",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="regionprofilesnippet",
            name="title_ar",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="regionprofilesnippet",
            name="title_en",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="regionprofilesnippet",
            name="title_es",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="regionprofilesnippet",
            name="title_fr",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
