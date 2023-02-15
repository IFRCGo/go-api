# Generated by Django 3.2.17 on 2023-02-15 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dref', '0049_auto_20221227_0501'),
    ]

    operations = [
        migrations.AddField(
            model_name='dref',
            name='type_of_dref',
            field=models.IntegerField(blank=True, choices=[(0, 'Imminent'), (1, 'Assessment'), (2, 'Response')], null=True, verbose_name='dref type'),
        ),
        migrations.RunSQL(
            sql=[("update dref_dref set type_of_dref = 2"),
                 ("update dref_dref set type_of_dref = 0 where type_of_onset=0"),
                 ("update dref_dref set type_of_dref = 1 where is_assessment_report"),],
            reverse_sql=[("update dref_dref set type_of_dref = NULL")],
        )
    ]
