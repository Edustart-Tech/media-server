# Generated by Django 5.1.6 on 2025-03-02 14:49

import django.db.models.deletion
import django.utils.timezone
import media_library.models
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="MediaCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("slug", models.SlugField(max_length=100, unique=True)),
            ],
            options={
                "verbose_name_plural": "Media Categories",
            },
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=254, unique=True, verbose_name="Email address"
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="MediaFile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=255)),
                ("file", models.FileField(upload_to=media_library.models.upload_to)),
                ("file_type", models.CharField(editable=False, max_length=100)),
                ("alt_text", models.CharField(blank=True, max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "is_html",
                    models.BooleanField(default=False, verbose_name="HTML Website"),
                ),
                (
                    "html_index_path",
                    models.CharField(blank=True, editable=False, max_length=255),
                ),
                (
                    "html_base_dir",
                    models.CharField(blank=True, editable=False, max_length=255),
                ),
                (
                    "original_zip_path",
                    models.CharField(blank=True, editable=False, max_length=255),
                ),
                ("is_processed", models.BooleanField(default=False, editable=False)),
                ("processing_error", models.TextField(blank=True, editable=False)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("width", models.IntegerField(editable=False, null=True)),
                ("height", models.IntegerField(editable=False, null=True)),
                (
                    "categories",
                    models.ManyToManyField(
                        blank=True, to="media_library.mediacategory"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MediaUsage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "content_type",
                    models.CharField(
                        help_text="Type of content where media is used (e.g. post, page)",
                        max_length=100,
                    ),
                ),
                (
                    "object_id",
                    models.CharField(
                        help_text="ID of the object where media is used", max_length=100
                    ),
                ),
                (
                    "field_name",
                    models.CharField(
                        help_text="Field name that uses the media", max_length=100
                    ),
                ),
                (
                    "url",
                    models.URLField(
                        blank=True, help_text="External link to where media is used"
                    ),
                ),
                ("date_added", models.DateTimeField(auto_now_add=True)),
                (
                    "media",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="usage_locations",
                        to="media_library.mediafile",
                    ),
                ),
            ],
            options={
                "verbose_name": "Media Usage",
                "verbose_name_plural": "Media Usages",
                "unique_together": {
                    ("media", "content_type", "object_id", "field_name")
                },
            },
        ),
    ]
