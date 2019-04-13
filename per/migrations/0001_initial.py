# Generated by Django 2.0.12 on 2019-04-13 14:41

from django.db import migrations, models
import django.db.models.deletion
import enumfields.fields
import per.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Form',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10)),
                ('name', models.CharField(max_length=100)),
                ('language', enumfields.fields.EnumIntegerField(enum=per.models.Language)),
                ('user', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('finalized', models.BooleanField(default=False)),
                ('ip_address', models.GenericIPAddressField(default='192.168.0.1')),
            ],
            options={
                'ordering': ('code', 'name', 'language', 'created_at'),
            },
        ),
        migrations.CreateModel(
            name='FormData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_id', models.CharField(max_length=10)),
                ('selected_option', enumfields.fields.EnumIntegerField(enum=per.models.Status)),
                ('notes', models.TextField()),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='per.Form')),
            ],
            options={
                'verbose_name': 'Form Data',
                'verbose_name_plural': 'Form Data',
                'ordering': ('form', 'question_id'),
            },
        ),
    ]
