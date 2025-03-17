# media_library/views.py
import mimetypes
import os

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Q
from django.views.static import serve

from .models import MediaFile, MediaCategory
from .forms import MediaFileForm, MediaFileCategoryForm
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
    """
    try:
        media_file = get_object_or_404(MediaFile, pk=media_id)

        # Ensure this is an HTML site
        if not media_file.is_html or not media_file.html_base_dir:
            raise Http404("Not an HTML website")

        # If no specific path is requested, serve the index.html
        if not path:
            # Find the relative path from the base directory to the index.html file
            rel_path = os.path.relpath(
                os.path.join(settings.MEDIA_ROOT, media_file.html_index_path),
                os.path.join(settings.MEDIA_ROOT, media_file.html_base_dir)
            )
            path = rel_path

        # Construct the full path to the requested file
        file_path = os.path.normpath(os.path.join(
            settings.MEDIA_ROOT, media_file.html_base_dir, path
        ))

        # Security check to prevent directory traversal attacks
        base_path = os.path.normpath(os.path.join(
            settings.MEDIA_ROOT, media_file.html_base_dir
        ))
        if not os.path.abspath(file_path).startswith(os.path.abspath(base_path)):
            raise Http404("Invalid path")

        # Check if the requested file exists
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            raise Http404("File not found")

        # Determine the content type
        content_type, encoding = mimetypes.guess_type(file_path)
        content_type = content_type or 'application/octet-stream'

        # Create a response with the file content
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)

        # Add security headers to allow loading assets from same origin
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['Content-Security-Policy'] = "frame-ancestors 'self'"

        # Disable caching for development (optional)
        if settings.DEBUG:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response

    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error serving HTML site: {e}")
        raise Http404("Error serving HTML site")