# Generated by Django 3.2.23 on 2024-01-31 19:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0188_auto_20240109_0508'),
        ('per', '0095_opslearning_appeal_document_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opslearning',
            name='appeal_code',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.appeal', to_field='code', verbose_name='appeal (MDR) code'),
        ),
    ]
