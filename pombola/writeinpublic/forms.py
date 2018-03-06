from django import forms
from django.forms import SelectMultiple, ModelMultipleChoiceField

from pombola.core.models import Person

from .client import WriteInPublic


class RecipientForm(forms.Form):
    persons = ModelMultipleChoiceField(queryset=None)

    # Dynamic queryset so we can show either people or committees
    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset')
        super(RecipientForm, self).__init__(*args, **kwargs)
        self.fields['persons'].queryset = queryset


class DraftForm(forms.Form):
    author_name = forms.CharField()
    author_email = forms.EmailField()
    subject = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)


class PreviewForm(forms.Form):
    pass
