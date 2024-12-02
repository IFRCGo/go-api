# Generated by Django 4.2.16 on 2024-12-02 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("local_units", "0018_localunit_deprecated_reason_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="localunit",
            name="is_deprecated",
            field=models.BooleanField(default=False, verbose_name="Is deprecated?"),
        ),
        migrations.AlterField(
            model_name="localunit",
            name="status",
            field=models.IntegerField(choices=[(1, "Verified"), (2, "Unverified")], default=2, verbose_name="status"),
        ),
        migrations.AlterField(
            model_name="localunitchangerequest",
            name="triggered_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Triggered at"),
        ),
    ]
