# Generated by Django 2.2.13 on 2020-06-18 09:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import per.models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('per', '0019_auto_20190716_1422'),
    ]

    operations = [
        migrations.AlterField(
            model_name='draft',
            name='code',
            field=models.CharField(max_length=10, verbose_name='code'),
        ),
        migrations.AlterField(
            model_name='draft',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.Country', verbose_name='country'),
        ),
        migrations.AlterField(
            model_name='draft',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='created at'),
        ),
        migrations.AlterField(
            model_name='draft',
            name='data',
            field=models.TextField(blank=True, null=True, verbose_name='data'),
        ),
        migrations.AlterField(
            model_name='draft',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
        migrations.AlterField(
            model_name='form',
            name='code',
            field=models.CharField(max_length=10, verbose_name='code'),
        ),
        migrations.AlterField(
            model_name='form',
            name='comment',
            field=models.TextField(blank=True, null=True, verbose_name='comment'),
        ),
        migrations.AlterField(
            model_name='form',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.Country', verbose_name='country'),
        ),
        migrations.AlterField(
            model_name='form',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='created at'),
        ),
        migrations.AlterField(
            model_name='form',
            name='ended_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='ended at'),
        ),
        migrations.AlterField(
            model_name='form',
            name='finalized',
            field=models.BooleanField(default=False, verbose_name='finalized'),
        ),
        migrations.AlterField(
            model_name='form',
            name='ip_address',
            field=models.GenericIPAddressField(default='192.168.0.1', verbose_name='IP address'),
        ),
        migrations.AlterField(
            model_name='form',
            name='language',
            field=models.IntegerField(choices=per.models.Language.choices, default=0, verbose_name='language'),
        ),
        migrations.AlterField(
            model_name='form',
            name='name',
            field=models.CharField(max_length=100, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='form',
            name='ns',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='NS'),
        ),
        migrations.AlterField(
            model_name='form',
            name='started_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='started at'),
        ),
        migrations.AlterField(
            model_name='form',
            name='submitted_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='submitted at'),
        ),
        migrations.AlterField(
            model_name='form',
            name='unique_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='unique id'),
        ),
        migrations.AlterField(
            model_name='form',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='updated at'),
        ),
        migrations.AlterField(
            model_name='form',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
        migrations.AlterField(
            model_name='form',
            name='validated',
            field=models.BooleanField(default=False, verbose_name='validated'),
        ),
        migrations.AlterField(
            model_name='formdata',
            name='form',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='per.Form', verbose_name='form'),
        ),
        migrations.AlterField(
            model_name='formdata',
            name='notes',
            field=models.TextField(verbose_name='notes'),
        ),
        migrations.AlterField(
            model_name='formdata',
            name='question_id',
            field=models.CharField(max_length=10, verbose_name='question id'),
        ),
        migrations.AlterField(
            model_name='formdata',
            name='selected_option',
            field=models.IntegerField(choices=per.models.Status.choices, default=0, verbose_name='selected option'),
        ),
        migrations.AlterField(
            model_name='nicedocument',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='perdoc_country', to='api.Country', verbose_name='country'),
        ),
        migrations.AlterField(
            model_name='nicedocument',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='created at'),
        ),
        migrations.AlterField(
            model_name='nicedocument',
            name='document',
            field=models.FileField(blank=True, null=True, upload_to=per.models.nice_document_path, verbose_name='document'),
        ),
        migrations.AlterField(
            model_name='nicedocument',
            name='document_url',
            field=models.URLField(blank=True, verbose_name='document url'),
        ),
        migrations.AlterField(
            model_name='nicedocument',
            name='name',
            field=models.CharField(max_length=100, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='nicedocument',
            name='visibility',
            field=models.IntegerField(default=1, choices=per.models.Visibilities.choices, verbose_name='visibility'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='approximate_date_next_capacity_assmt',
            field=models.DateTimeField(verbose_name='approximate date next capacity assessment'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='branch_involved',
            field=models.CharField(blank=True, max_length=90, null=True, verbose_name='branch involved'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asmt_country', to='api.Country', verbose_name='country'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='date_of_current_capacity_assessment',
            field=models.DateTimeField(verbose_name='date of current capacity assessment'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='date_of_last_capacity_assessment',
            field=models.DateTimeField(blank=True, null=True, verbose_name='date of last capacity assessment'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='date_of_mid_term_review',
            field=models.DateTimeField(verbose_name='date of mid term review'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='facilitated_by',
            field=models.CharField(blank=True, max_length=90, null=True, verbose_name='facilitated by'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='facilitator_email',
            field=models.CharField(blank=True, max_length=90, null=True, verbose_name='facilitated email'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='focal_point_email',
            field=models.CharField(blank=True, max_length=90, null=True, verbose_name='focal point email'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='focal_point_name',
            field=models.CharField(blank=True, max_length=90, null=True, verbose_name='focal point name'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='focus',
            field=models.CharField(blank=True, max_length=90, null=True, verbose_name='focus'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='had_previous_assessment',
            field=models.BooleanField(default=False, verbose_name='had previous assessment'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='phone_number',
            field=models.CharField(blank=True, max_length=90, null=True, verbose_name='phone number'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='skype_address',
            field=models.CharField(blank=True, max_length=90, null=True, verbose_name='skype address'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='type_of_capacity_assessment',
            field=models.IntegerField(default=0, choices=per.models.CAssessmentType.choices, verbose_name='type of capacity assessment'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='type_of_last_capacity_assessment',
            field=models.IntegerField(default=0, choices=per.models.CAssessmentType.choices, verbose_name='type of last capacity assessment'),
        ),
        migrations.AlterField(
            model_name='overview',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='actions',
            field=models.CharField(blank=True, max_length=900, null=True, verbose_name='actions'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='benchmark',
            field=models.CharField(blank=True, max_length=900, null=True, verbose_name='benchmark'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='code'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='comments',
            field=models.CharField(blank=True, max_length=900, null=True, verbose_name='comments'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='components',
            field=models.CharField(blank=True, max_length=900, null=True, verbose_name='components'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.Country', verbose_name='country'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='focal_point',
            field=models.CharField(blank=True, max_length=90, null=True, verbose_name='focal point'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='prioritization',
            field=models.IntegerField(choices=per.models.PriorityValue.choices, default=0, verbose_name='prioritization'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='question_id',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='question id'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='status',
            field=models.IntegerField(choices=per.models.WorkPlanStatus.choices, default=0, verbose_name='status'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='support_required',
            field=models.BooleanField(default=False, verbose_name='support required'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='timeline',
            field=models.DateTimeField(verbose_name='timeline'),
        ),
        migrations.AlterField(
            model_name='workplan',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
    ]
