# media_library/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import MediaCategory, MediaFile

@admin.register(MediaCategory)
class MediaCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'is_html', 'file_preview', 'uploaded_at')
    list_filter = ('file_type', 'is_html', 'categories', 'uploaded_at')
    search_fields = ('title', 'description', 'alt_text')
    readonly_fields = ('file_preview', 'file_type', 'html_index_path', 'width', 'height', 'uploaded_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'file', 'is_html', 'alt_text', 'description', 'categories')
        }),
        ('File Information', {
            'fields': ('file_preview', 'file_type', 'html_index_path', 'width', 'height', 'uploaded_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def file_preview(self, obj):
        if obj.file_type == 'image':
            return format_html('<img src="{}" height="50" />', obj.thumbnail.url)
        elif obj.file_type == 'html':
            return format_html('<span class="file-icon">🌐</span>')
        elif obj.file_type == 'document':
            return format_html('<span class="file-icon">📄</span>')
        elif obj.file_type == 'video':
            return format_html('<span class="file-icon">🎬</span>')

    # file_preview.short_description = 'Preview'
