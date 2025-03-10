from rest_framework import serializers

from media_library.models import MediaCategory, MediaFile


class MediaFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(method_name='get_url')
    category_name = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = MediaFile
        fields = "__all__"
        read_only_fields = (
            "id",
            "html_index_path",
            "html_base_dir",
            "original_zip_path",
            "is_processed",
            "processing_error",
            "uploaded_at",
            "updated_at",
            "width",
            "height",
            # "thumbnail",
            # "medium",
        )

    def get_url(self, obj):
        request = self.context.get("request")
        if obj.file is None:
            return None
        return request.build_absolute_uri(obj.file.url)

    def validate(self, attrs):
        attrs.pop("category_name", None)
        return super().validate(attrs)

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        if category_name := self.initial_data.get("category_name"):
            category, _ = MediaCategory.objects.get_or_create(name=category_name)
            instance.categories.add(category)
