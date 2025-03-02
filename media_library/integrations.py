# media_library/integrations.py
from django.urls import reverse
from .models import MediaFile

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
