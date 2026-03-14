# media_library/views.py
import mimetypes
import os

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

from .models import MediaFile, MediaCategory
from .forms import MediaFileForm
from .tasks import logger


def media_library(request):
    # Get query parameters for filtering
    query = request.GET.get('q', '')
    file_type = request.GET.get('type', '')
    category = request.GET.get('category', '')
    allowed_types = request.GET.get('allowed_types', '')


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

    if allowed_types:
        allowed_types = allowed_types.split(',')
        media_files = media_files.filter(file_type__in=allowed_types)

    # Pagination
    paginator = Paginator(media_files, 24)  # 24 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get categories for filter dropdown
    categories = MediaCategory.objects.all()

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'file_type': file_type,
        'category': category,
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request, 'media_library/media_library.html', context)

def media_upload(request):
    if request.method == 'POST':
        form = MediaFileForm(request.POST, request.FILES)
        if form.is_valid():
            media_file = form.save()
            messages.success(request, 'Media file uploaded successfully.')
            return redirect('media_library:media_detail', pk=media_file.pk)
    else:
        form = MediaFileForm()

    return render(request, 'media_library/media_upload.html', {'form': form})

def media_detail(request, pk):
    media_file = get_object_or_404(MediaFile, pk=pk)
    # Check if HTML file is still processing
    processing = media_file.is_html and not media_file.html_index_path
    return render(request, 'media_library/media_detail.html', {
        'media_file': media_file,
        'MEDIA_URL': settings.MEDIA_URL,
        'processing': processing,
    })

@login_required
def media_edit(request, pk):
    media_file = get_object_or_404(MediaFile, pk=pk)

    if request.method == 'POST':
        form = MediaFileForm(request.POST, request.FILES, instance=media_file)
        if form.is_valid():
            form.save()
            messages.success(request, 'Media file updated successfully.')
            return redirect('media_library:media_detail', pk=media_file.pk)
    else:
        form = MediaFileForm(instance=media_file)

    return render(request, 'media_library/media_edit.html', {
        'form': form,
        'media_file': media_file
    })

@login_required
def media_delete(request, pk):
    media_file = get_object_or_404(MediaFile, pk=pk)

    if request.method == 'POST':
        media_file.delete()
        messages.success(request, 'Media file deleted successfully.')
        return redirect('media_library:media_library')

    return render(request, 'media_library/media_delete.html', {'media_file': media_file})

def media_category(request, slug):
    category = get_object_or_404(MediaCategory, slug=slug)
    media_files = MediaFile.objects.filter(categories=category).order_by('-uploaded_at')

    # Pagination
    paginator = Paginator(media_files, 24)  # 24 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'media_library/media_category.html', {
        'category': category,
        'page_obj': page_obj,
    })


def serve_html_site(request, media_id, path=''):
    """
    Serve HTML website files with proper path resolution and security headers.
    Works with both local and S3 storage.
    """
    from django.core.files.storage import default_storage
    try:
        media_file = get_object_or_404(MediaFile, pk=media_id)

        # Ensure this is an HTML site
        if not media_file.is_html or not media_file.html_base_dir:
            raise Http404("Not an HTML website")

        # If no specific path is requested, serve the index.html
        if not path:
            path = os.path.relpath(
                media_file.html_index_path,
                media_file.html_base_dir
            )

        # Construct the relative path within the storage
        # Note: default_storage uses paths relative to MEDIA_ROOT
        relative_path = os.path.normpath(os.path.join(
            media_file.html_base_dir, path
        ))

        # Security check to prevent directory traversal attacks
        if not relative_path.startswith(media_file.html_base_dir):
            raise Http404("Invalid path")

        # Determine the content type
        content_type, _ = mimetypes.guess_type(relative_path)
        content_type = content_type or 'application/octet-stream'

        try:
            # Create a response with the file content from storage
            # We skip .exists() to reduce S3 latency (1 call instead of 2)
            file_obj = default_storage.open(relative_path, 'rb')
            response = FileResponse(file_obj, content_type=content_type)
        except Exception:
            # If the file doesn't exist or S3 fails
            raise Http404("File not found")

        # Add security headers to allow loading assets from same origin
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['Content-Security-Policy'] = "frame-ancestors 'self'"

        # Add caching headers for better performance on S3
        if not settings.DEBUG:
            # For assets (models, textures, scripts, etc.), cache for a long time (30 days)
            # For HTML files, cache for a short time (5 minutes)
            if content_type == 'text/html':
                response['Cache-Control'] = 'public, max-age=300'
            else:
                response['Cache-Control'] = 'public, max-age=2592000'
        else:
            # Disable caching for development
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response

    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error serving HTML site: {e}")
        raise Http404("Error serving HTML site")