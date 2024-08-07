# Generated by Django 2.0.5 on 2018-06-10 18:03

import django.db.models.deletion
from django.db import migrations, models

import api.models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_auto_20180607_1822"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminContact",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ctype", models.CharField(blank=True, max_length=100)),
                ("name", models.CharField(max_length=100)),
                ("title", models.CharField(max_length=300)),
                ("email", models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name="AdminKeyFigure",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("figure", models.CharField(max_length=100)),
                ("deck", models.CharField(max_length=50)),
                ("source", models.CharField(max_length=256)),
                ("visibility", models.IntegerField(default=3, choices=api.models.VisibilityChoices.choices)),
            ],
            options={
                "ordering": ("source",),
            },
        ),
        migrations.CreateModel(
            name="AdminLink",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=100)),
                ("url", models.URLField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name="CountrySnippet",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("snippet", models.TextField(blank=True, null=True)),
                ("image", models.ImageField(blank=True, null=True, upload_to="countries/%Y/%m/%d/")),
                ("visibility", models.IntegerField(default=3, choices=api.models.VisibilityChoices.choices)),
                (
                    "country",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="snippets", to="api.Country"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RegionSnippet",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("snippet", models.TextField(blank=True, null=True)),
                ("image", models.ImageField(blank=True, null=True, upload_to="regions/%Y/%m/%d/")),
                ("visibility", models.IntegerField(default=3, choices=api.models.VisibilityChoices.choices)),
                (
                    "region",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="snippets", to="api.Region"),
                ),
            ],
        ),
        migrations.AddField(
            model_name="snippet",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to=api.models.snippet_image_path),
        ),
        migrations.AddField(
            model_name="snippet",
            name="visibility",
            field=models.IntegerField(default=3, choices=api.models.VisibilityChoices.choices),
        ),
        migrations.AlterField(
            model_name="keyfigure",
            name="number",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name="snippet",
            name="snippet",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="CountryContact",
            fields=[
                (
                    "admincontact_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="api.AdminContact",
                    ),
                ),
                (
                    "country",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contacts", to="api.Country"),
                ),
            ],
            bases=("api.admincontact",),
        ),
        migrations.CreateModel(
            name="CountryKeyFigure",
            fields=[
                (
                    "adminkeyfigure_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="api.AdminKeyFigure",
                    ),
                ),
                (
                    "country",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="key_figures", to="api.Country"),
                ),
            ],
            bases=("api.adminkeyfigure",),
        ),
        migrations.CreateModel(
            name="CountryLink",
            fields=[
                (
                    "adminlink_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="api.AdminLink",
                    ),
                ),
                (
                    "country",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="links", to="api.Country"),
                ),
            ],
            bases=("api.adminlink",),
        ),
        migrations.CreateModel(
            name="RegionContact",
            fields=[
                (
                    "admincontact_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="api.AdminContact",
                    ),
                ),
                (
                    "region",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contacts", to="api.Region"),
                ),
            ],
            bases=("api.admincontact",),
        ),
        migrations.CreateModel(
            name="RegionKeyFigure",
            fields=[
                (
                    "adminkeyfigure_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="api.AdminKeyFigure",
                    ),
                ),
                (
                    "region",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="key_figures", to="api.Region"),
                ),
            ],
            bases=("api.adminkeyfigure",),
        ),
        migrations.CreateModel(
            name="RegionLink",
            fields=[
                (
                    "adminlink_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="api.AdminLink",
                    ),
                ),
                ("region", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="links", to="api.Region")),
            ],
            bases=("api.adminlink",),
        ),
    ]
