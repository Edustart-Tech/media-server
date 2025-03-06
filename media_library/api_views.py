# media_library/api_views.py
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
import json

from rest_framework.decorators import action
from rest_framework import viewsets


from .models import MediaCategory, MediaFile, MediaUsage
from .serializers import MediaFileSerializer

# @csrf_exempt
class MediaFileViewSet(viewsets.ModelViewSet):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer





@csrf_exempt
@require_POST
def upload_media(request):
    """API endpoint to upload a new media file."""
    try:
        # Get form data
        title = request.POST.get('title', '')
        file = request.FILES.get('file')
        alt_text = request.POST.get('alt_text', '')
        is_html = request.POST.get('is_html') == 'true'
        categories = request.POST.getlist('categories')
        # Validate file
        if not file:
            return JsonResponse({
                'success': False,
                'error': 'No file provided'
            }, status=400)

        # Create media file
        media_file = MediaFile(
            title=title or file.name,  # Use filename if no title provided
            file=file,
            alt_text=alt_text,
            is_html=is_html
        )

        # Save the file
        media_file.save()

        # Add categories
        if categories:
            for category_id in categories:
                try:
                    category = MediaCategory.objects.get(pk=category_id)
                    media_file.categories.add(category)
                except MediaCategory.DoesNotExist:
                    pass

        # Build response with URLs
        response_data = {
            'success': True,
            'id': media_file.id,
            'title': media_file.title,
            'url': request.build_absolute_uri(media_file.file.url),
            'file_type': media_file.file_type,
        }

        # Add thumbnail URLs for images
        if media_file.file_type == 'image':
            response_data.update({
                'thumbnail_url': request.build_absolute_uri(media_file.thumbnail.url),
                'medium_url': request.build_absolute_uri(media_file.medium.url),
            })

        # If HTML website, start processing in background
        if is_html and media_file.file.name.lower().endswith('.zip'):
            from .tasks import process_html_zip_file
            process_html_zip_file.send(media_file.id)
            response_data['message'] = 'HTML website is being processed'

        return JsonResponse(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_POST
def track_media_usage(request):
    """
    API endpoint to track media usage from external applications.

    Expects a JSON body with:
    {
        "media_id": 123,
        "content_type": "article",
        "object_id": "456",
        "field_name": "featured_image",
        "url": "https://example.com/article/456/" (optional)
    }
    """
    try:
        data = json.loads(request.body)

        # Validate required fields
        required_fields = ['media_id', 'content_type', 'object_id', 'field_name']
        if not all(field in data for field in required_fields):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)

        # Get media file
        try:
            media = MediaFile.objects.get(pk=data['media_id'])
        except MediaFile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f"Media with ID {data['media_id']} not found"
            }, status=404)

        # Create or update usage record
        usage, created = MediaUsage.objects.update_or_create(
            media=media,
            content_type=data['content_type'],
            object_id=data['object_id'],
            field_name=data['field_name'],
            defaults={'url': data.get('url', '')}
        )

        return JsonResponse({
            'success': True,
            'created': created
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_POST
def remove_media_usage(request):
    """
    API endpoint to remove media usage tracking.

    Expects a JSON body with:
    {
        "media_id": 123,
        "content_type": "article",
        "object_id": "456",
        "field_name": "featured_image" (optional - if not provided, all usages for this object are removed)
    }
    """
    try:
        data = json.loads(request.body)

        # Validate required fields
        required_fields = ['media_id', 'content_type', 'object_id']
        if not all(field in data for field in required_fields):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)

        # Build filter params
        filters = {
            'media_id': data['media_id'],
            'content_type': data['content_type'],
            'object_id': data['object_id'],
        }

        # Add field name filter if provided
        if 'field_name' in data:
            filters['field_name'] = data['field_name']

        # Delete matching usage records
        deleted, _ = MediaUsage.objects.filter(**filters).delete()

        return JsonResponse({
            'success': True,
            'deleted_count': deleted
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def media_list(request):
    """
    API endpoint to get a list of media files, with filtering options.

    Query parameters:
    - q: Search term
    - type: File type filter
    - category: Category slug filter
    - page: Page number
    - page_size: Number of items per page
    """
    # Get query parameters
    query = request.GET.get('q', '')
    file_type = request.GET.get('type', '')
    category = request.GET.get('category', '')
    page_number = request.GET.get('page', '1')
    page_size = request.GET.get('page_size', '24')

    # Start with all media files
    media_files = MediaFile.objects.all().order_by('-uploaded_at')

    # Apply filters
    if query:
        media_files = media_files.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(alt_text__icontains=query)
        )

    if file_type:
        media_files = media_files.filter(file_type=file_type)

    if category:
        media_files = media_files.filter(categories__slug=category)

    # Pagination
    try:
        page_number = int(page_number)
        page_size = min(int(page_size), 100)  # Limit max page size
    except ValueError:
        page_number = 1
        page_size = 24

    paginator = Paginator(media_files, page_size)
    page_obj = paginator.get_page(page_number)

    # Build response
    results = []
    for media in page_obj:
        media_data = {
            'id': media.id,
            'title': media.title,
            'file_type': media.file_type,
            'url': request.build_absolute_uri(media.file.url),
            'uploaded_at': media.uploaded_at.isoformat(),
        }

        # Add thumbnail URLs for images
        if media.file_type == 'image':
            media_data['thumbnail_url'] = request.build_absolute_uri(media.thumbnail.url)
            media_data['medium_url'] = request.build_absolute_uri(media.medium.url)

        results.append(media_data)

    return JsonResponse({
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'next': page_obj.has_next(),
        'previous': page_obj.has_previous(),
        'results': results
    })

def media_detail(request, pk):
    """
    API endpoint to get details for a specific media file.
    """
    try:
        media = MediaFile.objects.get(pk=pk)

        response = {
            'id': media.id,
            'title': media.title,
            'file_type': media.file_type,
            'url': request.build_absolute_uri(media.file.url),
            'alt_text': media.alt_text,
            'description': media.description,
            'uploaded_at': media.uploaded_at.isoformat(),
            'updated_at': media.updated_at.isoformat(),
            'categories': [
                {'name': c.name, 'slug': c.slug}
                for c in media.categories.all()
            ],
            'usage_count': media.usage_locations.count(),
        }

        # Add image-specific fields
        if media.file_type == 'image':
            response.update({
                'width': media.width,
                'height': media.height,
                'thumbnail_url': request.build_absolute_uri(media.thumbnail.url),
                'medium_url': request.build_absolute_uri(media.medium.url),
            })

        # Add HTML-specific fields
        if media.file_type == 'html' and media.html_index_path:
            response.update({
                'html_url': request.build_absolute_uri(
                    reverse('media_library:serve_html_site', kwargs={'media_id': media.id})
                ),
            })

        return JsonResponse(response)

    except MediaFile.DoesNotExist:
        return JsonResponse({
            'error': f"Media with ID {pk} not found"
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
def category_list(request):
    """API endpoint to get a list of all categories."""
    try:
        categories = MediaCategory.objects.all().order_by('name')
        results = [
            {
                'id': category.id,
                'name': category.name,
                'slug': category.slug
            }
            for category in categories
        ]

        return JsonResponse({
            'count': len(results),
            'results': results
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
