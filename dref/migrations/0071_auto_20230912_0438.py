# Generated by Django 3.2.20 on 2023-09-12 04:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dref", "0070_dreffinalreport_operation_end_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="dreffinalreport",
            name="regional_focal_point_email",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="regional focal point email"),
        ),
        migrations.AddField(
            model_name="dreffinalreport",
            name="regional_focal_point_name",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="regional focal point name"),
        ),
        migrations.AddField(
            model_name="dreffinalreport",
            name="regional_focal_point_phone_number",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="regional focal point phone number"),
        ),
        migrations.AddField(
            model_name="dreffinalreport",
            name="regional_focal_point_title",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="regional focal point title"),
        ),
    ]
