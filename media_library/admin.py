# media_library/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import MediaCategory, MediaFile, MediaUsage, User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Define admin model for custom User model with no username field."""

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


@admin.register(MediaCategory)
class MediaCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class MediaUsageInline(admin.TabularInline):
    model = MediaUsage
    extra = 0
    readonly_fields = ('date_added',)


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'is_html', 'file_preview', 'uploaded_at', 'usage_count')
    list_filter = ('file_type', 'is_html', 'categories', 'uploaded_at')
    search_fields = ('title', 'description', 'alt_text')
    readonly_fields = ('file_preview', 'file_type', 'html_index_path', 'width', 'height', 'uploaded_at', 'updated_at', 'usage_count')
    inlines = [MediaUsageInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'file', 'is_html', 'alt_text', 'description', 'categories')
        }),
        ('File Information', {
            'fields': ('file_preview', 'file_type', 'html_index_path', 'width', 'height', 'uploaded_at', 'updated_at'),
            'classes': ('collapse',),
        }),
        ('Usage Information', {
            'fields': ('usage_count',),
            'classes': ('collapse',),
        }),
    )

    def usage_count(self, obj):
        count = obj.usage_locations.count()
        return f"{count} location{'s' if count != 1 else ''}"

    usage_count.short_description = "Used in"

    def file_preview(self, obj):
        if obj.file_type == 'image':
            return format_html('<img src="{}" height="50" />', obj.thumbnail.url)
        elif obj.file_type == 'html':
            return format_html('<span class="file-icon">🌐</span>')
        elif obj.file_type == 'document':
            return format_html('<span class="file-icon">📄</span>')
        elif obj.file_type == 'video':
            return format_html('<span class="file-icon">🎬</span>')

    file_preview.short_description = 'Preview'

@admin.register(MediaUsage)
class MediaUsageAdmin(admin.ModelAdmin):
    list_display = ('media', 'content_type', 'object_id', 'field_name', 'date_added')
    list_filter = ('content_type', 'date_added')
    search_fields = ('media__title', 'content_type', 'object_id', 'field_name', 'url')
    raw_id_fields = ('media',)