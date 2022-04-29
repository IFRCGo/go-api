# Generated by Django 2.2.27 on 2022-04-29 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dref', '0009_remove_drefoperationalupdate_parent'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlannedInterventionIndicators',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('target', models.IntegerField(blank=True, null=True, verbose_name='Target')),
                ('actual', models.IntegerField(blank=True, null=True, verbose_name='Actual')),
            ],
            options={
                'verbose_name': 'planned intervention indicator',
                'verbose_name_plural': 'planned intervention indicators',
            },
        ),
        migrations.RemoveField(
            model_name='drefoperationalupdate',
            name='date_of_approval',
        ),
        migrations.RemoveField(
            model_name='plannedintervention',
            name='indicator',
        ),
        migrations.AddField(
            model_name='drefoperationalupdate',
            name='new_operational_start_date',
            field=models.DateField(blank=True, null=True, verbose_name='New Operation Start Date'),
        ),
        migrations.AddField(
            model_name='plannedintervention',
            name='female',
            field=models.IntegerField(blank=True, null=True, verbose_name='female'),
        ),
        migrations.AddField(
            model_name='plannedintervention',
            name='male',
            field=models.IntegerField(blank=True, null=True, verbose_name='male'),
        ),
        migrations.AddField(
            model_name='plannedintervention',
            name='progress_towards_outcome',
            field=models.TextField(blank=True, null=True, verbose_name='Progress Towards Outcome'),
        ),
    ]
