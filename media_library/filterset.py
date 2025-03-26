from django_filters import rest_framework

from media_library.models import MediaFile


class MediaFileFilter(rest_framework.FilterSet):
    file = rest_framework.CharFilter(field_name='file', lookup_expr='iexact')
    html_index_path = rest_framework.CharFilter(method='filter_html_index_path')

    class Meta:
        model = MediaFile
        fields = (
            "is_html",
            "html_base_dir",
            "file_type",
        )

    def filter_html_index_path(self, queryset, name, value):
        # This was the only way I could make html_index_path to accept multiple entry filtering
        value = self.data.getlist("html_index_path")
        if value:
            queryset = queryset.filter(html_index_path__in=value)
        return queryset