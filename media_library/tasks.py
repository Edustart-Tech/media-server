# media_library/tasks.py
import os
import zipfile
import shutil
from django.conf import settings
import dramatiq
from .models import MediaFile

@dramatiq.actor
def process_html_zip_file(media_id):
    """Process a zip file containing an HTML website."""
    try:
        media = MediaFile.objects.get(id=media_id)

        # Skip if not an HTML zip or already processed
        if not media.is_html or media.html_index_path:
            return

        # Get the file path
        file_path = media.file.path
        if not os.path.exists(file_path):
            return

        # Store original zip path
        media.original_zip_path = file_path

        # Create extraction directory
        extract_dir = os.path.join(settings.MEDIA_ROOT, f'html_sites/{media.id}')
        os.makedirs(extract_dir, exist_ok=True)

        # Extract the zip file
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find index.html
        index_path = None
        for root, dirs, files in os.walk(extract_dir):
            if 'index.html' in files:
                rel_path = os.path.relpath(os.path.join(root, 'index.html'), settings.MEDIA_ROOT)
                index_path = rel_path
                break

        # Update media file with index path
        if index_path:
            media.html_index_path = index_path
            media.save(update_fields=['html_index_path', 'original_zip_path'])

            # Delete the zip file to save space
            if os.path.exists(file_path):
                os.remove(file_path)

    except MediaFile.DoesNotExist:
        pass
    except Exception as e:
        # Log the error
        print(f"Error processing HTML zip file: {e}")

@dramatiq.actor
def cleanup_html_site(media_id):
    """Clean up extracted HTML site files when media is deleted."""
    extract_dir = os.path.join(settings.MEDIA_ROOT, f'html_sites/{media_id}')
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
