from django import forms

from pombola.writeinpublic.client import WriteInPublic


class MessageForm(forms.Form):
    author_name = forms.CharField()
    author_email = forms.EmailField()
    subject = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)
