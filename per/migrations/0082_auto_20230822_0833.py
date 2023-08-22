# Generated by Django 3.2.20 on 2023-08-22 08:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('per', '0081_auto_20230731_1426'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formcomponentquestionandanswer',
            name='answer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='per.formanswer', verbose_name='answer'),
        ),
        migrations.AlterField(
            model_name='formcomponentquestionandanswer',
            name='question',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='per.formquestion', verbose_name='question'),
        ),
    ]
