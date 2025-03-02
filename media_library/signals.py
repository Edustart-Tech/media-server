from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from media_library.models import MediaFile


# Signal handlers for background processing
@receiver(post_save, sender=MediaFile)
def trigger_media_processing(sender, instance, created, **kwargs):
    if instance.is_html and not instance.is_processed:
        from .tasks import process_html_zip_file
        process_html_zip_file.send(instance.id)
        # Mark as processed to avoid duplicate processing
        MediaFile.objects.filter(id=instance.id).update(is_processed=True)


@receiver(post_delete, sender=MediaFile)
def trigger_cleanup(sender, instance, **kwargs):
    if instance.is_html:
        from .tasks import cleanup_html_site
        cleanup_html_site.send(instance.id)