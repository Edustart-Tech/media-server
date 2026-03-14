import logging
import os
import zipfile


logger = logging.getLogger('media_library')


def process_html_zip_file_now(media):
    """
    Extracts HTML zip files into storage and identifies the index.html path.
    Handles Verge3D .xz compression by renaming and setting S3 metadata.
    """
    from django.core.files.storage import default_storage
    import io
    import mimetypes

    # Skip if not an HTML zip or already processed
    if not media.is_html or media.html_index_path:
        return

    logger.info(f"Processing HTML ZIP for media {media.id}")

    try:
        # Get the zip file content
        with media.file.open("rb") as f:
            zip_content = f.read()

        # Open the ZIP file from memory
        with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
            # Create extraction directory prefix
            extract_base = f"html_sites/{media.id}"

            index_path = None
            base_dir = None

            # Iterate through all files in the ZIP
            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    continue

                filename = file_info.filename
                is_compressed = False

                # Verge3D Fallback: If it ends in .xz, it's LZMA compressed
                if filename.endswith(".xz"):
                    filename = filename[:-3]  # Remove .xz extension
                    is_compressed = True

                # Construct the target path in storage
                target_path = os.path.join(extract_base, filename)

                # Save the file to storage
                with zip_ref.open(file_info) as source_file:
                    if default_storage.exists(target_path):
                        default_storage.delete(target_path)

                    content = source_file.read()

                    # Decompress .xz files with LZMA
                    if is_compressed:
                        import lzma

                        try:
                            content = lzma.decompress(content)
                        except lzma.LZMAError as e:
                            logger.error(f"Failed to decompress {filename}: {e}")
                            continue

                    # Upload with correct Content-Type via boto3 if on S3
                    if hasattr(default_storage, "bucket"):
                        content_type, _ = mimetypes.guess_type(target_path)
                        # Ensure .js files get the right type
                        ext = os.path.splitext(target_path)[1].lower()
                        if ext == ".js":
                            content_type = "application/javascript"
                        elif ext == ".wasm":
                            content_type = "application/wasm"
                        elif ext == ".gltf":
                            content_type = "model/gltf+json"
                        elif ext == ".css":
                            content_type = "text/css"
                        content_type = content_type or "application/octet-stream"

                        default_storage.bucket.put_object(
                            Key=target_path,
                            Body=content,
                            ContentType=content_type,
                        )
                    else:
                        from django.core.files.base import ContentFile

                        default_storage.save(target_path, ContentFile(content))

                # Identify index.html
                if filename.endswith("index.html"):
                    # The first index.html found (or highest in hierarchy)
                    if index_path is None or len(filename) < len(index_path):
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
