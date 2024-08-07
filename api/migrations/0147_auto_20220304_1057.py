# Generated by Django 2.2.27 on 2022-03-04 10:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0146_auto_20220228_0952"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="name",
            field=models.CharField(max_length=256, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="event",
            name="name_ar",
            field=models.CharField(max_length=256, null=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="event",
            name="name_en",
            field=models.CharField(max_length=256, null=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="event",
            name="name_es",
            field=models.CharField(max_length=256, null=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="event",
            name="name_fr",
            field=models.CharField(max_length=256, null=True, verbose_name="name"),
        ),
    ]
