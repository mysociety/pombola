from django import forms

class GlobalSearchForm(forms.Form):
    q = forms.CharField(
        label='Your search query',
        max_length=1024,
    )
