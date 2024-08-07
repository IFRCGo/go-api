# Generated by Django 3.2.23 on 2024-02-23 04:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("databank", "0021_countrykeyclimate"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fdrsincome",
            name="indicator",
            field=models.CharField(
                choices=[
                    ("h_gov_CHF", "Home Government"),
                    ("f_gov_CHF", "Foreign Government"),
                    ("ind_CHF", "Individual"),
                    ("corp_CHF", "Corporation"),
                    ("found_CHF", "Foundation"),
                    ("un_CHF", "UN Agencies"),
                    ("pooled_f_CHF", "Pooled funds"),
                    ("ngo_CHF", "Non Governmental Organization"),
                    ("si_CHF", "Service Income"),
                    ("iga_CHF", "Income Generating Activity"),
                    ("KPI_incomeFromNSsLC_CHF", "Other National Society"),
                    ("ifrc_CHF", "IFRC"),
                    ("icrc_CHF", "ICRC"),
                    ("other_CHF", "Other Source"),
                ],
                max_length=255,
                verbose_name="indicator",
            ),
        ),
    ]
