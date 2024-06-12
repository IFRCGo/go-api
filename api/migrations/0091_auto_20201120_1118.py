# Generated by Django 2.2.13 on 2020-11-20 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0090_auto_20201120_1045"),
    ]

    operations = [
        migrations.AddField(
            model_name="country",
            name="nsi_annual_fdrs_reporting",
            field=models.CharField(blank=True, max_length=16, verbose_name="Annual Reporting to FDRS"),
        ),
        migrations.AddField(
            model_name="country",
            name="nsi_branches",
            field=models.CharField(blank=True, max_length=16, verbose_name="Branches"),
        ),
        migrations.AddField(
            model_name="country",
            name="nsi_cmc_dashboard_compliance",
            field=models.CharField(blank=True, max_length=16, verbose_name="Complying with CMC Dashboard"),
        ),
        migrations.AddField(
            model_name="country",
            name="nsi_domestically_generated_income",
            field=models.CharField(blank=True, max_length=16, verbose_name=">50% Domestically Generated Income"),
        ),
        migrations.AddField(
            model_name="country",
            name="nsi_expenditures",
            field=models.CharField(blank=True, max_length=16, verbose_name="Expenditures (CHF)"),
        ),
        migrations.AddField(
            model_name="country",
            name="nsi_gov_financial_support",
            field=models.CharField(blank=True, max_length=16, verbose_name="Gov Financial Support"),
        ),
        migrations.AddField(
            model_name="country",
            name="nsi_income",
            field=models.CharField(blank=True, max_length=16, verbose_name="Income (CHF)"),
        ),
        migrations.AddField(
            model_name="country",
            name="nsi_policy_implementation",
            field=models.CharField(blank=True, max_length=16, verbose_name="Your Policy / Programme Implementation"),
        ),
        migrations.AddField(
            model_name="country",
            name="nsi_risk_management_framework",
            field=models.CharField(blank=True, max_length=16, verbose_name="Risk Management Framework"),
        ),
        migrations.AddField(
            model_name="country",
            name="nsi_staff",
            field=models.CharField(blank=True, max_length=16, verbose_name="Staff"),
        ),
        migrations.AddField(
            model_name="country",
            name="nsi_trained_in_first_aid",
            field=models.CharField(blank=True, max_length=16, verbose_name="Trained in First Aid"),
        ),
        migrations.AddField(
            model_name="country",
            name="nsi_volunteers",
            field=models.CharField(blank=True, max_length=16, verbose_name="Volunteers"),
        ),
        migrations.AddField(
            model_name="country",
            name="nsi_youth",
            field=models.CharField(blank=True, max_length=16, verbose_name="Youth - 6-19 Yrs"),
        ),
        migrations.AddField(
            model_name="country",
            name="wash_kit10",
            field=models.IntegerField(null=True, verbose_name="WASH Kit10"),
        ),
        migrations.AddField(
            model_name="country",
            name="wash_kit2",
            field=models.IntegerField(null=True, verbose_name="WASH Kit2"),
        ),
        migrations.AddField(
            model_name="country",
            name="wash_kit5",
            field=models.IntegerField(null=True, verbose_name="WASH Kit5"),
        ),
        migrations.AddField(
            model_name="country",
            name="wash_ndrt_trained",
            field=models.IntegerField(null=True, verbose_name="NDRT Trained"),
        ),
        migrations.AddField(
            model_name="country",
            name="wash_rdrt_trained",
            field=models.IntegerField(null=True, verbose_name="RDRT Trained"),
        ),
        migrations.AddField(
            model_name="country",
            name="wash_staff_at_branch",
            field=models.IntegerField(null=True, verbose_name="WASH Staff at Branch"),
        ),
        migrations.AddField(
            model_name="country",
            name="wash_staff_at_hq",
            field=models.IntegerField(null=True, verbose_name="WASH Staff at HQ"),
        ),
        migrations.AddField(
            model_name="country",
            name="wash_total_staff",
            field=models.IntegerField(null=True, verbose_name="Total WASH Staff"),
        ),
    ]
