# Generated by Django 2.2.27 on 2022-07-25 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dref", "0017_auto_20220725_0538"),
    ]

    operations = [
        migrations.AddField(
            model_name="dref",
            name="is_surge_personnel_deployed",
            field=models.BooleanField(blank=True, null=True, verbose_name="Is surge personnel deployed"),
        ),
    ]
