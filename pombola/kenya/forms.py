from django import forms
from django.forms.widgets import Textarea

class CountyPerformancePetitionForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Your name'}))
    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Your email address'}))

class CountyPerformanceSenateForm(forms.Form):
    comments = forms.CharField(
        label='Tell the senate what you think',
        widget=Textarea(
            attrs={
                'rows': 5,
                'cols': 60,
                'placeholder': 'Add any comments here'}))
