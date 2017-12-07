from django import forms
from django.forms import SelectMultiple, ModelMultipleChoiceField

from pombola.writeinpublic.client import WriteInPublic
from pombola.core.models import Person


class RecipientForm(forms.Form):
    persons = ModelMultipleChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super(RecipientForm, self).__init__(*args, **kwargs)
        self.fields['persons'].queryset = Person.objects.filter(
            identifiers__scheme='everypolitician',
            identifiers__identifier__isnull=False,
        )


class DraftForm(forms.Form):
    author_name = forms.CharField()
    author_email = forms.EmailField()
    subject = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)


class PreviewForm(forms.Form):
    pass
