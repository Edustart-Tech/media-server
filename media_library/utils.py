import logging
import os
import zipfile

from django.conf import settings

logger = logging.getLogger('media_library')


def process_html_zip_file_now(media):
    # Skip if not an HTML zip or already processed
    if not media.is_html or media.html_index_path:
        return

    # Get the file path
    file_path = media.file.path
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return

    # Store original zip path
    media.original_zip_path = file_path

    # Create extraction directory - use media_id to avoid conflicts
    extract_dir = os.path.join(settings.MEDIA_ROOT, f'html_sites/{media.id}')
    os.makedirs(extract_dir, exist_ok=True)

    logger.info(f"Extracting ZIP file to {extract_dir}")

    try:
        # Extract the zip file
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find index.html (could be in the root or in a subdirectory)
        index_path = None
        base_dir = None
        for root, dirs, files in os.walk(extract_dir):
            if 'index.html' in files:
                # Get the relative path to MEDIA_ROOT
                rel_path = os.path.relpath(os.path.join(root, 'index.html'), settings.MEDIA_ROOT)
                index_path = rel_path
                # Also store the base directory of the index.html file
                base_dir = os.path.relpath(root, settings.MEDIA_ROOT)
                break

        # Update media file with paths
        if index_path:
            media.html_index_path = index_path
            # Store the base directory of the HTML site
            media.html_base_dir = base_dir
            return media
        else:
            logger.error(f"No index.html found in ZIP file: {file_path}")

    except Exception as e:
        logger.error(f"Error extracting ZIP file: {e}")
        raise
