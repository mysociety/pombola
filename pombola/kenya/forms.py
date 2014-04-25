from django import forms
from django.forms.widgets import Textarea


class ExperimentFormFields(forms.Form):
    user_key = forms.CharField(widget=forms.HiddenInput())
    variant = forms.CharField(widget=forms.HiddenInput())
    # This field represents gender information passed from
    # Facebook, and should be either 'm', 'f' or '?'.
    g = forms.CharField(widget=forms.HiddenInput())
    # This field represents age group information passed from
    # Facebook, which is either 'under' (under some threshold),
    # 'over' (over some threshold) or '?'.
    agroup = forms.CharField(widget=forms.HiddenInput())


class CountyPerformancePetitionForm(ExperimentFormFields, forms.Form):
    name = forms.CharField(
        error_messages={'required': 'You must enter a name'},
        widget=forms.TextInput(
            attrs={
                'required': 'required',
                'placeholder': 'Your name'}))
    email = forms.EmailField(
        error_messages={'required': 'You must enter a valid email address'},
        widget=forms.TextInput(
            attrs={
                'required': 'required',
                'placeholder': 'Your email address'}))

    def clean(self):
        # We want to provide a single helpful error message if both
        # name and email address aren't supplied, so override clean to
        # detect that condition
        cleaned_data = super(CountyPerformancePetitionForm,
                             self).clean()
        if not cleaned_data:
            raise forms.ValidationError(
                "You must specify a name and a valid email address")
        return cleaned_data


class CountyPerformanceSenateForm(ExperimentFormFields, forms.Form):
    comments = forms.CharField(
        label='Tell the senate what you think',
        error_messages={'required': "You didn't enter a comment"},
        widget=Textarea(
            attrs={
                'rows': 5,
                'cols': 60,
                'required': 'required',
                'placeholder': 'Add any comments here'}))
