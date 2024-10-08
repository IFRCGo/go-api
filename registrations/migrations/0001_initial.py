# Generated by Django 4.2.16 on 2024-10-08 07:30

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="DomainWhitelist",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("domain_name", models.CharField(max_length=200, verbose_name="domain name")),
                ("description", models.TextField(blank=True, null=True, verbose_name="description")),
                ("is_active", models.BooleanField(default=True, verbose_name="is active?")),
            ],
            options={
                "verbose_name": "Domain Whitelist",
                "verbose_name_plural": "Domains Whitelist",
            },
        ),
        migrations.CreateModel(
            name="Pending",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("token", models.CharField(editable=False, max_length=32, verbose_name="token")),
                (
                    "admin_contact_1",
                    models.EmailField(blank=True, editable=False, max_length=254, null=True, verbose_name="admin contact 1"),
                ),
                (
                    "admin_contact_2",
                    models.EmailField(blank=True, editable=False, max_length=254, null=True, verbose_name="admin contact 2"),
                ),
                ("admin_token_1", models.CharField(editable=False, max_length=32, null=True, verbose_name="admin token 1")),
                ("admin_token_2", models.CharField(editable=False, max_length=32, null=True, verbose_name="admin token 2")),
                ("admin_1_validated", models.BooleanField(default=False, editable=False, verbose_name="admin 1 validated")),
                ("admin_2_validated", models.BooleanField(default=False, editable=False, verbose_name="admin 2 validated")),
                (
                    "admin_1_validated_date",
                    models.DateTimeField(blank=True, editable=False, null=True, verbose_name="admin 1 validated date"),
                ),
                (
                    "admin_2_validated_date",
                    models.DateTimeField(blank=True, editable=False, null=True, verbose_name="admin 2 validated date"),
                ),
                ("email_verified", models.BooleanField(default=False, editable=False, verbose_name="email verified?")),
                ("justification", models.CharField(blank=True, max_length=500, null=True, verbose_name="justification")),
                (
                    "reminder_sent_to_admin",
                    models.BooleanField(default=False, editable=False, verbose_name="reminder sent to admin?"),
                ),
            ],
            options={
                "verbose_name": "Pending user",
                "verbose_name_plural": "Pending users",
            },
        ),
        migrations.CreateModel(
            name="UserExternalToken",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="title")),
                (
                    "jti",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, help_text="Unique identifier for the token", unique=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("expire_timestamp", models.DateTimeField(verbose_name="expire timestamp")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="user"
                    ),
                ),
            ],
            options={
                "verbose_name": "User External Token",
                "verbose_name_plural": "User External Tokens",
            },
        ),
        migrations.CreateModel(
            name="Recovery",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("token", models.CharField(editable=False, max_length=32, verbose_name="token")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="user"
                    ),
                ),
            ],
            options={
                "verbose_name": "Recovery",
                "verbose_name_plural": "Recoveries",
            },
        ),
    ]
