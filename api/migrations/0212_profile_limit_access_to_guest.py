# Generated by Django 4.2.13 on 2024-07-30 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0211_alter_countrydirectory_unique_together_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="limit_access_to_guest",
            field=models.BooleanField(
                default=True,
                help_text="If this value is set to true, the user is treated as a guest user regardless of any other permissions they may have, thereby depriving them of all non-guest user permissions.",
                verbose_name="limit access to guest user permissions",
            ),
        ),
    ]
