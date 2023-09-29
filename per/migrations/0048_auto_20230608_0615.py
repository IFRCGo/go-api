# Generated by Django 3.2.19 on 2023-06-08 06:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('per', '0047_auto_20230510_0527'),
    ]

    operations = [
        migrations.CreateModel(
            name='AreaResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='per.formarea', verbose_name='Area')),
            ],
        ),
        migrations.CreateModel(
            name='CustomPerWorkPlanComponent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actions', models.TextField(blank=True, max_length=900, null=True, verbose_name='Actions')),
                ('due_date', models.DateField(blank=True, null=True, verbose_name='Due date')),
                ('status', models.IntegerField(choices=[(0, 'standby'), (1, 'ongoing'), (2, 'cancelled'), (3, 'delayed'), (4, 'pending'), (5, 'need improvements'), (6, 'finished'), (7, 'approved'), (8, 'closed')], default=0, verbose_name='status')),
            ],
        ),
        migrations.CreateModel(
            name='FormComponentConsiderations',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('urban_considerations', models.TextField(blank=True, null=True, verbose_name='Urban Considerations')),
                ('epi_considerations', models.TextField(blank=True, null=True, verbose_name='Epi Considerations')),
                ('climate_environmental_conisderations', models.TextField(blank=True, null=True, verbose_name='Climate Environmental Considerations')),
            ],
        ),
        migrations.RemoveField(
            model_name='formcomponent',
            name='climate_environmental_conisderations',
        ),
        migrations.RemoveField(
            model_name='formcomponent',
            name='epi_considerations',
        ),
        migrations.RemoveField(
            model_name='formcomponent',
            name='urban_considerations',
        ),
        migrations.RemoveField(
            model_name='perworkplan',
            name='custom_component',
        ),
        migrations.RemoveField(
            model_name='perworkplancomponent',
            name='area',
        ),
        migrations.CreateModel(
            name='PerAssessment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area_response', models.ManyToManyField(blank=True, to='per.AreaResponse', verbose_name='Area Response')),
                ('overview', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='per.overview', verbose_name='PerAssessment')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
        ),
        migrations.CreateModel(
            name='FormComponentQuestionAndAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('answer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='per.formanswer', verbose_name='answer')),
                ('question', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='per.formquestion', verbose_name='question')),
            ],
        ),
        migrations.AddField(
            model_name='arearesponse',
            name='component_response',
            field=models.ManyToManyField(blank=True, to='per.FormComponent', verbose_name='Component Response'),
        ),
        migrations.AddField(
            model_name='formcomponent',
            name='consideration_responses',
            field=models.ManyToManyField(blank=True, to='per.FormComponentConsiderations', verbose_name='Consideration responses'),
        ),
        migrations.AddField(
            model_name='formcomponent',
            name='question_responses',
            field=models.ManyToManyField(blank=True, to='per.FormComponentQuestionAndAnswer', verbose_name='Question responses'),
        ),
        migrations.AddField(
            model_name='perworkplan',
            name='custom_component_responses',
            field=models.ManyToManyField(blank=True, to='per.CustomPerWorkPlanComponent', verbose_name='Custom Per-WorkPlan Component'),
        ),
    ]
