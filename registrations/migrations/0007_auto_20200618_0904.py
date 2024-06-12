# Generated by Django 2.2.13 on 2020-06-18 09:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registrations", "0006_domainwhitelist_description"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="domainwhitelist",
            options={"verbose_name": "Domain Whitelist", "verbose_name_plural": "Domains Whitelist"},
        ),
        migrations.AlterModelOptions(
            name="recovery",
            options={"verbose_name": "Recovery", "verbose_name_plural": "Recoveries"},
        ),
        migrations.AlterField(
            model_name="domainwhitelist",
            name="description",
            field=models.TextField(blank=True, null=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="domainwhitelist",
            name="domain_name",
            field=models.CharField(max_length=200, verbose_name="domain name"),
        ),
        migrations.AlterField(
            model_name="domainwhitelist",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="is active?"),
        ),
        migrations.AlterField(
            model_name="pending",
            name="admin_1_validated",
            field=models.BooleanField(default=False, editable=False, verbose_name="admin 1 validated"),
        ),
        migrations.AlterField(
            model_name="pending",
            name="admin_1_validated_date",
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name="admin 1 validated date"),
        ),
        migrations.AlterField(
            model_name="pending",
            name="admin_2_validated",
            field=models.BooleanField(default=False, editable=False, verbose_name="admin 2 validated"),
        ),
        migrations.AlterField(
            model_name="pending",
            name="admin_2_validated_date",
            field=models.DateTimeField(blank=True, editable=False, null=True, verbose_name="admin 2 validated date"),
        ),
        migrations.AlterField(
            model_name="pending",
            name="admin_contact_1",
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name="admin contact 1"),
        ),
        migrations.AlterField(
            model_name="pending",
            name="admin_contact_2",
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name="admin contact 2"),
        ),
        migrations.AlterField(
            model_name="pending",
            name="admin_token_1",
            field=models.CharField(editable=False, max_length=32, null=True, verbose_name="admin token 1"),
        ),
        migrations.AlterField(
            model_name="pending",
            name="admin_token_2",
            field=models.CharField(editable=False, max_length=32, null=True, verbose_name="admin token 2"),
        ),
        migrations.AlterField(
            model_name="pending",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created at"),
        ),
        migrations.AlterField(
            model_name="pending",
            name="email_verified",
            field=models.BooleanField(default=False, editable=False, verbose_name="email verified?"),
        ),
        migrations.AlterField(
            model_name="pending",
            name="token",
            field=models.CharField(editable=False, max_length=32, verbose_name="token"),
        ),
        migrations.AlterField(
            model_name="pending",
            name="user",
            field=models.OneToOneField(
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                primary_key=True,
                serialize=False,
                to=settings.AUTH_USER_MODEL,
                verbose_name="user",
            ),
        ),
        migrations.AlterField(
            model_name="recovery",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created at"),
        ),
        migrations.AlterField(
            model_name="recovery",
            name="token",
            field=models.CharField(editable=False, max_length=32, verbose_name="token"),
        ),
        migrations.AlterField(
            model_name="recovery",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="user"
            ),
        ),
    ]
