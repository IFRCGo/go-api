# Generated by Django 3.2.25 on 2024-05-07 05:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('local_units', '0012_auto_20240506_0636'),
    ]

    operations = [
        migrations.AddField(
            model_name='localunittype',
            name='colour',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Local Unit Colour'),
        ),
    ]
