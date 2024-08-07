# Generated by Django 2.0.5 on 2018-06-26 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registrations", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="pending",
            old_name="admin_token",
            new_name="admin_token_1",
        ),
        migrations.AddField(
            model_name="pending",
            name="admin_1_validated",
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name="pending",
            name="admin_2_validated",
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name="pending",
            name="admin_token_2",
            field=models.CharField(editable=False, max_length=32, null=True),
        ),
    ]
