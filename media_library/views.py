# media_library/views.py
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Q

from .models import MediaFile, MediaCategory
from .forms import MediaFileForm, MediaFileCategoryForm

def media_library(request):
    # Get query parameters for filtering
    query = request.GET.get('q', '')
    file_type = request.GET.get('type', '')
    category = request.GET.get('category', '')

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
    }

    return render(request, 'media_library/media_library.html', context)

@login_required
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
    return render(request, 'media_library/media_detail.html', {
        'media_file': media_file,
        'MEDIA_URL': settings.MEDIA_URL,
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
