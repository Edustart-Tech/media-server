# media_library/models.py
import os
import shutil
import zipfile

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils import timezone
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

def upload_to(instance, filename):
    # Organize files by year/month
    now = timezone.now()
    base, extension = os.path.splitext(filename)
    extension = extension.lower()

    return f'{now.year}/{now.month}/{slugify(base)}{extension}'


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    # use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser, PermissionsMixin):
    """Custom User model that uses email instead of username."""

    username = None
    email = models.EmailField("Email address", unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class MediaCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Media Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class MediaUsage(models.Model):
    """Model to track where media files are used"""
    media = models.ForeignKey('MediaFile', on_delete=models.CASCADE, related_name='usage_locations')
    content_type = models.CharField(max_length=100, help_text="Type of content where media is used (e.g. post, page)")
    object_id = models.CharField(max_length=100, help_text="ID of the object where media is used")
    field_name = models.CharField(max_length=100, help_text="Field name that uses the media")
    url = models.URLField(blank=True, help_text="External link to where media is used")
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Media Usage"
        verbose_name_plural = "Media Usages"
        unique_together = ('media', 'content_type', 'object_id', 'field_name')

    def __str__(self):
        return f"{self.media.title} used in {self.content_type} ({self.field_name})"


class MediaFile(models.Model):
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to=upload_to)
    file_type = models.CharField(max_length=100, editable=False)
    alt_text = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(MediaCategory, blank=True)

    # For Verge3d files
    is_html = models.BooleanField(default=False, verbose_name="HTML Website")
    html_index_path = models.CharField(max_length=255, blank=True, editable=False)
    html_base_dir = models.CharField(max_length=255, blank=True, editable=False)
    original_zip_path = models.CharField(max_length=255, blank=True, editable=False)

    # Processing status
    is_processed = models.BooleanField(default=False, editable=False)
    processing_error = models.TextField(blank=True, editable=False)

    # Auto-generated fields
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Image specific fields (will be null for non-image files)
    width = models.IntegerField(null=True, editable=False)
    height = models.IntegerField(null=True, editable=False)

    # Thumbnails for images
    thumbnail = ImageSpecField(
        source='file',
        processors=[ResizeToFill(150, 150)],
        format='JPEG',
        options={'quality': 80}
    )

    medium = ImageSpecField(
        source='file',
        processors=[ResizeToFill(300, 300)],
        format='JPEG',
        options={'quality': 85}
    )

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    @classmethod
    def get_media_by_url(cls, media_url):
        if media_url.endswith('.html'):
            return cls.objects.get(html_index_path=media_url)
        return cls.objects.get(file=media_url)

    def save(self, *args, **kwargs):
        # Set title from filename if not provided
        if not self.title and self.file:
            # Get filename without extension and path
            filename = os.path.basename(self.file.name)
            base_name, _ = os.path.splitext(filename)
            # Convert to title case and replace underscores/hyphens with spaces
            self.title = base_name.replace('_', ' ').replace('-', ' ').title()

        if self.file:
            # Set file_type based on extension
            extension = os.path.splitext(self.file.name)[1].lower()[1:]

            image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            document_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
            video_extensions = ['mp4', 'avi', 'mov', 'wmv']
            audio_extensions = ['mp3', 'wav', 'ogg']

            if extension in image_extensions:
                self.file_type = 'image'
            elif extension in document_extensions:
                self.file_type = 'document'
            elif extension in video_extensions:
                self.file_type = 'video'
            elif extension in audio_extensions:
                self.file_type = 'audio'
            elif self.is_html and extension == 'zip':
                self.file_type = 'html'
            else:
                self.file_type = 'other'

        super().save(*args, **kwargs)
