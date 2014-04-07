from django import forms

class CountyPerformancePetitionForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Your name'}))
    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Your email address'}))
