# Generated by Django 3.2.18 on 2023-05-08 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("per", "0044_auto_20230508_0535"),
    ]

    operations = [
        migrations.AlterField(
            model_name="overview",
            name="date_of_assessment",
            field=models.DateField(verbose_name="date of assessment"),
        ),
        migrations.AlterField(
            model_name="overview",
            name="date_of_mid_term_review",
            field=models.DateField(blank=True, null=True, verbose_name="estimated date of mid term review"),
        ),
        migrations.AlterField(
            model_name="overview",
            name="date_of_next_asmt",
            field=models.DateField(blank=True, null=True, verbose_name="estimated date of next assessment"),
        ),
        migrations.AlterField(
            model_name="overview",
            name="date_of_orientation",
            field=models.DateField(blank=True, null=True, verbose_name="Date of Orientation"),
        ),
        migrations.AlterField(
            model_name="overview",
            name="date_of_previous_assessment",
            field=models.DateField(blank=True, null=True, verbose_name="Date of previous assessment"),
        ),
        migrations.AlterField(
            model_name="overview",
            name="workplan_development_date",
            field=models.DateField(blank=True, null=True, verbose_name="Workplan Development Date"),
        ),
        migrations.AlterField(
            model_name="overview",
            name="workplan_revision_date",
            field=models.DateField(blank=True, null=True, verbose_name="Workplan Revision Date"),
        ),
    ]
