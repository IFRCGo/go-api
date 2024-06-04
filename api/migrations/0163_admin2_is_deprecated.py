# Generated by Django 3.2.18 on 2023-04-12 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0162_admin2_created_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="admin2",
            name="is_deprecated",
            field=models.BooleanField(default=False, help_text="Is this a deprecated area?"),
        ),
    ]
