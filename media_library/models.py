# media_library/models.py
import os
import zipfile

from django.conf import settings
from django.db import models
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

class MediaFile(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=upload_to)
    file_type = models.CharField(max_length=100, editable=False)
    alt_text = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField(MediaCategory, blank=True)

    # For Verge3d files
    is_html = models.BooleanField(default=False, verbose_name="HTML Website")
    html_index_path = models.CharField(max_length=255, blank=True, editable=False)

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

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
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

        # First save to ensure we have an ID and the file is stored
        super().save(*args, **kwargs)

        # Handle HTML website upload (unzip)
        if self.is_html and extension == 'zip' and not self.html_index_path:
            self._extract_html_website()
            # Save again to store the html_index_path
            super().save(update_fields=['html_index_path'])

    def _extract_html_website(self):
        """Extract the zip file and find the index.html file."""
        if not self.file:
            return

        # Get the file path on the server
        file_path = self.file.path

        # Create extraction directory - use media_id to avoid conflicts
        extract_dir = os.path.join(settings.MEDIA_ROOT, f'html_sites/{self.id}')
        os.makedirs(extract_dir, exist_ok=True)

        # Extract the zip file
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find index.html (could be in the root or in a subdirectory)
        index_path = None
        for root, dirs, files in os.walk(extract_dir):
            if 'index.html' in files:
                # Get the relative path to MEDIA_ROOT
                rel_path = os.path.relpath(os.path.join(root, 'index.html'), settings.MEDIA_ROOT)
                index_path = rel_path
                break

        # Store the path to index.html relative to MEDIA_URL
        if index_path:
            self.html_index_path = index_path
        else:
            # No index.html found
            self.html_index_path = ''
