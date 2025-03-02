# media_library/integrations.py
from django.urls import reverse
from .models import MediaFile, MediaUsage


class MediaLibraryIntegration:
    @staticmethod
    def get_media_chooser_url():
        """Return URL for the media chooser popup"""
        return reverse('media_library:media_library') + '?popup=1'

    @staticmethod
    def get_media_by_id(media_id):
        """Get a media file by ID"""
        try:
            return MediaFile.objects.get(pk=media_id)
        except MediaFile.DoesNotExist:
            return None

    @staticmethod
    def get_media_url(media_id, size='original'):
        """
        Get URL for a media file with specified size
        size options: 'original', 'thumbnail', 'medium'
        """
        media = MediaLibraryIntegration.get_media_by_id(media_id)
        if not media:
            return None

        if size == 'thumbnail' and media.file_type == 'image':
            return media.thumbnail.url
        elif size == 'medium' and media.file_type == 'image':
            return media.medium.url
        else:
            return media.file.url

    @staticmethod
    def get_media_for_template(media_id):
        """
        Returns a dictionary with all media details for use in templates
        """
        media = MediaLibraryIntegration.get_media_by_id(media_id)
        if not media:
            return None

        return {
            'id': media.id,
            'title': media.title,
            'file_type': media.file_type,
            'alt_text': media.alt_text,
            'description': media.description,
            'url': media.file.url,
            'thumbnail_url': media.thumbnail.url if media.file_type == 'image' else None,
            'medium_url': media.medium.url if media.file_type == 'image' else None,
        }


    @staticmethod
    def get_html_site_url(media_id):
        """Get URL for an HTML website"""
        from django.urls import reverse
        return reverse('media_library:serve_html_site', kwargs={'media_id': media_id})

    @staticmethod
    def track_media_usage(media_id, content_type, object_id, field_name, url=None):
        """
        Track where a media file is being used

        Parameters:
        - media_id: ID of the MediaFile
        - content_type: Type of content (e.g. 'post', 'page', 'product')
        - object_id: ID of the object where media is used
        - field_name: Name of the field that references the media
        - url: Optional URL where the media is displayed
        """
        try:
            media = MediaFile.objects.get(pk=media_id)

            # Create or update usage record
            usage, created = MediaUsage.objects.update_or_create(
                media=media,
                content_type=content_type,
                object_id=str(object_id),
                field_name=field_name,
                defaults={'url': url or ''}
            )

            return True
        except MediaFile.DoesNotExist:
            return False

    @staticmethod
    def remove_media_usage(media_id, content_type, object_id, field_name=None):
        """
        Remove a usage tracking record when media is no longer used

        If field_name is None, removes all usage records for this object
        """
        try:
            filters = {
                'media_id': media_id,
                'content_type': content_type,
                'object_id': str(object_id),
            }

            if field_name:
                filters['field_name'] = field_name

            MediaUsage.objects.filter(**filters).delete()
            return True
        except Exception:
            return False