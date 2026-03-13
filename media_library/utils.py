import logging
import os
import zipfile


logger = logging.getLogger('media_library')


def process_html_zip_file_now(media):
    """
    Extracts HTML zip files into storage and identifies the index.html path.
    Works with both local and S3 storage.
    """
    from django.core.files.storage import default_storage
    import io

    # Skip if not an HTML zip or already processed
    if not media.is_html or media.html_index_path:
        return

    logger.info(f"Processing HTML ZIP for media {media.id}")

    try:
        # Get the zip file content
        # Use media.file.open() to handle both local and S3
        with media.file.open('rb') as f:
            zip_content = f.read()
        
        # Open the ZIP file from memory
        with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_ref:
            # Create extraction directory prefix
            extract_base = f'html_sites/{media.id}'
            
            index_path = None
            base_dir = None
            
            # Iterate through all files in the ZIP
            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    continue
                
                # Construct the target path in storage
                target_path = os.path.join(extract_base, file_info.filename)
                
                # Save the file to storage
                with zip_ref.open(file_info) as source_file:
                    if default_storage.exists(target_path):
                        default_storage.delete(target_path)
                    default_storage.save(target_path, source_file)
                
                # Identify index.html
                if file_info.filename.endswith('index.html'):
                    # The first index.html found (or highest in hierarchy)
                    if index_path is None or len(file_info.filename) < len(index_path):
                        index_path = target_path
                        base_dir = os.path.dirname(target_path)

        # Update media file with paths
        if index_path:
            media.html_index_path = index_path
            media.html_base_dir = base_dir
            media.is_processed = True
            logger.info(f"Successfully processed HTML site: index={index_path}")
            return media
        else:
            logger.error(f"No index.html found in ZIP for media {media.id}")
            media.processing_error = "No index.html found in ZIP file"

    except Exception as e:
        logger.error(f"Error processing HTML ZIP for media {media.id}: {e}")
        media.processing_error = str(e)
        raise

    return media
