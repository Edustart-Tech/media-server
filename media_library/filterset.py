from django_filters import rest_framework

from media_library.models import MediaFile


class MediaFileFilter(rest_framework.FilterSet):
    file = rest_framework.CharFilter(field_name='file', lookup_expr='iexact')
    class Meta:
        model = MediaFile
        fields = (
            "is_html",
            "html_index_path",
            "html_base_dir",
            "file_type",
        )