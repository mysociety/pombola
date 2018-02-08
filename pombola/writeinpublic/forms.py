from django import forms
from django.forms import SelectMultiple, ModelMultipleChoiceField

from pombola.core.models import Person

from .client import WriteInPublic


class RecipientForm(forms.Form):
    persons = ModelMultipleChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super(RecipientForm, self).__init__(*args, **kwargs)
        # This is set dynamically because the script which syncs
        # EveryPolitician UUIDs is run at a regular interval, and we want to
        # pick up any new people that appear.
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
