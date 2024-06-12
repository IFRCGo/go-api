# Generated by Django 3.2.18 on 2023-04-18 07:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dref", "0055_auto_20230406_1010"),
    ]

    operations = [
        migrations.AddField(
            model_name="dref",
            name="regional_focal_point_email",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="regional focal point email"),
        ),
        migrations.AddField(
            model_name="dref",
            name="regional_focal_point_name",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="regional focal point name"),
        ),
        migrations.AddField(
            model_name="dref",
            name="regional_focal_point_phone_number",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="regional focal point phone number"),
        ),
        migrations.AddField(
            model_name="dref",
            name="regional_focal_point_title",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="regional focal point title"),
        ),
        migrations.AddField(
            model_name="drefoperationalupdate",
            name="regional_focal_point_email",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="regional focal point email"),
        ),
        migrations.AddField(
            model_name="drefoperationalupdate",
            name="regional_focal_point_name",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="regional focal point name"),
        ),
        migrations.AddField(
            model_name="drefoperationalupdate",
            name="regional_focal_point_phone_number",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="regional focal point phone number"),
        ),
        migrations.AddField(
            model_name="drefoperationalupdate",
            name="regional_focal_point_title",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="regional focal point title"),
        ),
    ]
