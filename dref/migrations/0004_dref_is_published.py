# Generated by Django 2.2.27 on 2022-03-31 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dref", "0003_auto_20220314_0824"),
    ]

    operations = [
        migrations.AddField(
            model_name="dref",
            name="is_published",
            field=models.BooleanField(default=False, verbose_name="Is published"),
        ),
    ]
