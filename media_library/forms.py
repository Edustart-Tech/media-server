# media_library/forms.py
from django import forms
from .models import MediaFile, MediaCategory

class MediaFileForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        fields = ['title', 'file', 'is_html', 'alt_text', 'description', 'categories']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'categories': forms.CheckboxSelectMultiple(),
        }
        help_texts = {
            'title': 'Leave empty to use the file name',
            'is_html': 'Check this if uploading a zip file containing a website with an index.html file',
        }


class MediaFileCategoryForm(forms.ModelForm):
    class Meta:
        model = MediaCategory
        fields = ['name', 'slug']
