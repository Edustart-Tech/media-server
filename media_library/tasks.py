# media_library/tasks.py
import logging
import os
import shutil
from django.conf import settings
import dramatiq
from .utils import process_html_zip_file_now

logger = logging.getLogger('media_library')


@dramatiq.actor
def process_html_zip_file(media_id):
    """Process a zip file containing an HTML website."""
    # Import here to avoid AppRegistryNotReady errors
    from .models import MediaFile

    try:
        media = MediaFile.objects.get(id=media_id)
        media = process_html_zip_file_now(media)
        if media:
            media.save(update_fields=['html_index_path', 'original_zip_path', 'html_base_dir'])
    except MediaFile.DoesNotExist:
        logger.warning(f"MediaFile with ID {media_id} not found")
    except Exception as e:
        logger.error(f"Error processing HTML zip file: {e}")

@dramatiq.actor
def cleanup_html_site(media_id):
    """Clean up extracted HTML site files when media is deleted."""
    extract_dir = os.path.join(settings.MEDIA_ROOT, f'html_sites/{media_id}')
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
