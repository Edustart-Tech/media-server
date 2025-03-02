# media_library/forms.py
from django import forms
from .models import MediaFile, MediaCategory

class MediaFileForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        fields = ['title', 'file', 'alt_text', 'description', 'categories']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'categories': forms.CheckboxSelectMultiple(),
        }

class MediaFileCategoryForm(forms.ModelForm):
    class Meta:
        model = MediaCategory
        fields = ['name', 'slug']
