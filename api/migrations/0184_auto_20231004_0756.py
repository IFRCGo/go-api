# Generated by Django 3.2.20 on 2023-10-04 07:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0183_auto_20230928_0635"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="ctype_ar",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="ctype_en",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="ctype_es",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="ctype_fr",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="email_ar",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="email_en",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="email_es",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="email_fr",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="name_ar",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="name_en",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="name_es",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="name_fr",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="phone_ar",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="phone_en",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="phone_es",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="phone_fr",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="title_ar",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="title_en",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="title_es",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="title_fr",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="translation_module_original_language",
        ),
        migrations.RemoveField(
            model_name="fieldreportcontact",
            name="translation_module_skip_auto_translation",
        ),
    ]
