from django import forms
from django.forms import SelectMultiple, ModelMultipleChoiceField, ModelChoiceField

from pombola.core.models import Person

from .client import WriteInPublic


class RecipientForm(forms.Form):
    # Dynamicly create fields so we can show either people or committees
    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset')
        multiple = kwargs.pop('multiple', True)
        super(RecipientForm, self).__init__(*args, **kwargs)
        if multiple:
            self.fields['persons'] = ModelMultipleChoiceField(queryset=queryset)
        else:
            self.fields['persons'] = ModelChoiceField(queryset=queryset)


class DraftForm(forms.Form):
    author_name = forms.CharField()
    author_email = forms.EmailField()
    subject = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)


class PreviewForm(forms.Form):
    pass
