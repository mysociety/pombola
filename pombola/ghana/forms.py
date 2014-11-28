from django import forms
from django.core.files.uploadedfile import UploadedFile

from pombola.ghana import models

class UploadForm(forms.ModelForm):
    name = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean(self):
        file = self.cleaned_data.get('file')
        if isinstance(file, UploadedFile):
            self.cleaned_data['name'] = file.name
        else:
            del self.cleaned_data['name']
        return self.cleaned_data

    class Meta:
        model = models.UploadModel


class InfoPageUpload(forms.ModelForm):
    name = forms.CharField(required=False, widget=forms.HiddenInput)
    title = forms.CharField()

    def clean(self):
        file = self.cleaned_data.get('file')
        if isinstance(file, UploadedFile):
            self.cleaned_data['name'] = file.name
        else:
            del self.cleaned_data['name']
        return self.cleaned_data

    class Meta:
        model = models.UploadModel

